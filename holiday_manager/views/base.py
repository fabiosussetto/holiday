from django.shortcuts import render
from django.views import generic
from django.contrib.messages.api import get_messages
from holiday_manager import models
from holiday_manager import forms
from invites import forms as invite_forms
from django.shortcuts import redirect
from django.db import transaction
from django.core.urlresolvers import reverse
from holiday_manager.views.generic import LoginRequiredViewMixin
from django.contrib import messages

def home(request, **kwargs):
    return render(request, 'holiday_manager/index.html')
    
def error(request, **kwargs):
    messages = get_messages(request)
    return render(request, 'error.html', {'messages': messages})
    
    
class ProjectViewMixin(object):
    
    curr_project = None
    main_section = None
    active_section = None
    active_view = None
    
    def dispatch(self, request, *args, **kwargs):
        self.curr_project = models.Project.objects.get(slug=kwargs['project'])
        if not request.user.is_authenticated() or request.user.project_id != self.curr_project.pk:
            return redirect(reverse('app:invites:login', kwargs={'project': self.curr_project.slug}))
            
        return super(ProjectViewMixin, self).dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        queryset = super(ProjectViewMixin, self).get_queryset()
        return queryset.filter(project=self.curr_project)
        
    def render_to_response(self, context, **response_kwargs):
        data = {
            'curr_project': self.curr_project,
            'active_section': self.active_section,
            'main_section': self.main_section,
            'active_view': self.__class__.__name__.lower()
        }
        data.update(context)
        return super(ProjectViewMixin, self).render_to_response(data, **response_kwargs)
        
    def get_form_kwargs(self):
        kwargs = super(ProjectViewMixin, self).get_form_kwargs()
        if issubclass(self.get_form_class(), forms.ProjectFormMixin):
            kwargs.update({'project': self.curr_project})
        return kwargs
        
    def form_valid(self, form):
        res = super(ProjectViewMixin, self).form_valid(form)
        messages.success(self.request, "Changes has been successfully saved.")
        return res

    def form_invalid(self, form):
        res = super(ProjectViewMixin, self).form_invalid(form)
        messages.error(self.request, "Please correct the errors and retry.")
        return res

    
class CreateProject(generic.CreateView):
    model = models.Project
    template_name = 'holiday_manager/public/project_register.html'
    object = None
    
    def get_forms(self):
        kwargs = {'initial': self.get_initial()}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return invite_forms.SignupForm(**kwargs), forms.CreateProjectForm(**kwargs)
    
    def get(self, request, *args, **kwargs):
        signup_form, project_form = self.get_forms()
        return self.render_to_response(self.get_context_data(
            signup_form=signup_form, project_form=project_form
        ))
        
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        signup_form, project_form = self.get_forms()
        if project_form.is_valid() and signup_form.is_valid():
            project = project_form.save()
            signup_form.instance.project = project
            user = signup_form.save()
            return redirect(reverse('app:dashboard', kwargs={'project': project.slug}))
        else:
            return self.render_to_response(self.get_context_data(
                signup_form=signup_form, project_form=project_form
            ))
