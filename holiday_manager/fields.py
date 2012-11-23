from django.db import models
from django import forms
from django.core import exceptions
from django.core import validators
from django.utils.text import capfirst

class ListFormField(forms.TypedMultipleChoiceField):

    def __init__(self, *args, **kwargs):
        super(ListFormField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        value = super(ListFormField, self).clean(value)
        if value is None:
            return []
        return ",".join([str(x) for x in value])
    
class ListField(models.CommaSeparatedIntegerField):
    """
    Field to simplify the handling of a multiple choice of None->all days.
    
    Stores as CSInt.
    """
    __metaclass__ = models.SubfieldBase
    
    description = "CSV list Field"
    default_validators = []
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 200
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
        defaults = {'required': not self.blank,
                    'label': capfirst(self.verbose_name),
                    'choices': self.choices,
                    'help_text': self.help_text}
        defaults.update(kwargs)
        return ListFormField(**defaults) 
    
    def to_python(self, value):
        if isinstance(value, basestring):
            if value:
                value = [int(x) for x in value.split(',') if x]
            else:
                value = []
        elif value is None:
            value = []
        return value

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is None:
            return None
        return ",".join([str(x) for x in value])
    
    
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], [r'^holiday_manager.fields.ListField'])
except ImportError:
    pass