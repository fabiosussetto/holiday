from django.shortcuts import redirect
from django.db.models import ForeignKey
from django import forms

def redirect_to_referer(request):
    return redirect(request.META.get('HTTP_REFERER', None))
    
    
class ProjectRelated(ForeignKey):
    
    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        if isinstance(self.rel.to, basestring):
            raise ValueError("Cannot create form field for %r yet, because "
                             "its related model %r has not been loaded yet" %
                             (self.name, self.rel.to))
        defaults = {
            'form_class': forms.ModelChoiceField,
            'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to),
            'to_field_name': self.rel.field_name,
        }
        defaults.update(kwargs)
        return super(ForeignKey, self).formfield(**defaults)

        
class Choices(object):
    """
    A class to encapsulate handy functionality for lists of choices
    for a Django model field.

    Each argument to ``Choices`` is a choice, represented as either a
    string, a two-tuple, or a three-tuple.

    If a single string is provided, that string is used as the
    database representation of the choice as well as the
    human-readable presentation.

    If a two-tuple is provided, the first item is used as the database
    representation and the second the human-readable presentation.

    If a triple is provided, the first item is the database
    representation, the second a valid Python identifier that can be
    used as a readable label in code, and the third the human-readable
    presentation. This is most useful when the database representation
    must sacrifice readability for some reason: to achieve a specific
    ordering, to use an integer rather than a character field, etc.

    Regardless of what representation of each choice is originally
    given, when iterated over or indexed into, a ``Choices`` object
    behaves as the standard Django choices list of two-tuples.

    If the triple form is used, the Python identifier names can be
    accessed as attributes on the ``Choices`` object, returning the
    database representation. (If the single or two-tuple forms are
    used and the database representation happens to be a valid Python
    identifier, the database representation itself is available as an
    attribute on the ``Choices`` object, returning itself.)

    """

    def __init__(self, *choices):
        self._full = []
        self._choices = []
        self._choice_dict = {}
        for choice in self.equalize(choices):
            self._full.append(choice)
            self._choices.append((choice[0], choice[2]))
            self._choice_dict[choice[1]] = choice[0]

    def equalize(self, choices):
        for choice in choices:
            if isinstance(choice, (list, tuple)):
                if len(choice) == 3:
                    yield choice
                elif len(choice) == 2:
                    yield (choice[0], choice[0], choice[1])
                else:
                    raise ValueError("Choices can't handle a list/tuple of length %s, only 2 or 3"
                                     % len(choice))
            else:
                yield (choice, choice, choice)

    def __iter__(self):
        return iter(self._choices)

    def __getattr__(self, attname):
        try:
            return self._choice_dict[attname]
        except KeyError:
            raise AttributeError(attname)

    def __getitem__(self, index):
        return self._choices[index]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                          ', '.join(("%s" % str(i) for i in self._full)))