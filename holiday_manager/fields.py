from django.db import models
from django import forms

def validate_csv(data):
    return True
    #return all(map(lambda x:isinstance(x, int), data))
    
class ListFormField(forms.TypedMultipleChoiceField):

    def __init__(self, *args, **kwargs):
        super(ListFormField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        value = super(ListFormField, self).clean(value)
        return ",".join([str(x) for x in value])
    
class ListField(models.CommaSeparatedIntegerField):
    """
    Field to simplify the handling of a multiple choice of None->all days.
    
    Stores as CSInt.
    """
    __metaclass__ = models.SubfieldBase
    
    description = "CSV list Field"
    default_validators = [validate_csv]
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 200
        #self.mchoices = kwargs['choices']
        super(ListField, self).__init__(*args, **kwargs)
        
    def validate(self, value, model_instance):
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        if self._choices and value:
            for item in value:
                for option_key, option_value in self.choices:
                    if isinstance(option_value, (list, tuple)):
                        # This is an optgroup, so look inside the group for
                        # options.
                        for optgroup_key, optgroup_value in option_value:
                            if item == optgroup_key:
                                return
                    elif item == option_key:
                        return
            msg = self.error_messages['invalid_choice'] % value
            raise exceptions.ValidationError(msg)

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])
    
    def formfield(self, **kwargs):
        kwargs['choices'] = self.choices
        return ListFormField(**kwargs) 
    
    def to_python(self, value):
        if isinstance(value, basestring):
            if value:
                value = [int(x) for x in value.split(',') if x]
            else:
                value = []
        return value

    def get_db_prep_value(self, value, connection=None, prepared=False):
        return ",".join([str(x) for x in value])
    
    
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], [r'^holiday_manager.fields.ListField'])
except ImportError:
    pass