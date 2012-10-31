from django.shortcuts import render
from django.views import generic
from django.contrib.messages.api import get_messages
from holiday_manager import models
from holiday_manager import forms
from invites import forms as invite_forms
from django.shortcuts import redirect
from django.db import transaction
from django.core.urlresolvers import reverse

def home(request, **kwargs):
    return render(request, 'holiday_manager/index.html')
    
def error(request, **kwargs):
    messages = get_messages(request)
    return render(request, 'error.html', {'messages': messages})
    
    
class ProjectView(generic.TemplateView):
    
    curr_project = None
    
    def dispatch(self, *args, **kwargs):
        self.curr_project = models.Project.objects.get(slug=kwargs['project'])
        return super(ProjectView, self).dispatch(*args, **kwargs)
        
    def render_to_response(self, context, **response_kwargs):
        if not 'curr_project' in context:
            context['curr_project'] = self.curr_project
        return super(ProjectView, self).render_to_response(context, **response_kwargs)

    
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
