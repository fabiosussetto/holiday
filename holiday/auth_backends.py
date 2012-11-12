from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from holiday_manager.models import Project

class CustomUserModelBackend(ModelBackend):

    def authenticate(self, email=None, password=None, project=None, project_slug=None, skip_password=False):
        # TODO: make project_slug mandatory! Maybe pass a project obj instead
        try:
            if project_slug:
                project = Project.objects.get(slug=project_slug)
            else:
                assert project
            user = self.user_class.objects.get(email=email, project=project)
            if skip_password:
                return user
            if user.check_password(password):
                return user
        except (self.user_class.DoesNotExist, Project.DoesNotExist):
            return None

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        except self.user_class.DoesNotExist:
            return None

    @property
    def user_class(self):
        if not hasattr(self, '_user_class'):
            self._user_class = get_model(*settings.CUSTOM_USER_MODEL.split('.', 2))
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
        return self._user_class