from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import generic

class LoginRequiredViewMixin(object):
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredViewMixin, self).dispatch(*args, **kwargs)
        
        
class FilteredListView(generic.ListView):

    kind_arg = 'kind'
    kind = None
    kind_values = []
    model_kind_field = None
    kind_default = 'all'
    
    def get(self, request, *args, **kwargs):
        kind = kwargs.get(self.kind_arg, self.kind_default) or self.kind_default
        self.kind_values = list(self.kind_values)
        self.kind_values.append(self.kind_default)
        if kind != self.kind_default and kind not in self.kind_values:
            raise ImproperlyConfigured("Invalid kind param '%s' for '%s'. (Allowed: %s)"
                                       % kind, self.__class__.__name__, self.kind_values)
        
        self.kind = kind
        return super(FilteredListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilteredListView, self).get_context_data(**kwargs)
        context.update({'list_kind': self.kind})
        return context
        
    def get_queryset(self):
        if self.kind == self.kind_default:
            return super(FilteredListView, self).get_queryset()
            
        queryset_method = getattr(self, 'get_%s_queryset' % self.kind, None)
        if queryset_method:
            return queryset_method(self.kind)
            
        if not self.model_kind_field:
            raise ImproperlyConfigured("Please define a 'model_kind_field' for '%s'."
                        % self.__class__.__name__)
        
        queryset = super(FilteredListView, self).get_queryset()
        query_args = {self.model_kind_field: self.kind}
        return queryset.filter(**query_args)
        
    @classmethod
    def url_params(cls):
        options = list(cls.kind_values)
        options.append(cls.kind_default)
        return '|'.join(options)
