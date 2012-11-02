import factory
from invites.models import User
from holiday_manager.models import ApprovalGroup, ApprovalRule, HolidayRequest, Project
import datetime

class ProjectFactory(factory.Factory):
    name = 'Test project'
    slug = 'test-project'

class GroupFactory(factory.Factory):
    FACTORY_FOR = ApprovalGroup

class ApprovalRuleFactory(factory.Factory):
    FACTORY_FOR = ApprovalRule
    
class HolidayRequestFactory(factory.Factory):
    FACTORY_FOR = HolidayRequest
    requested_on = datetime.datetime.now().date()
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        request_days_ago = kwargs.pop('requested_days_ago', None)
        if request_days_ago:
            kwargs['requested_on'] = datetime.datetime.now().date() - datetime.timedelta(days=request_days_ago)
        req = super(HolidayRequestFactory, cls)._prepare(create, **kwargs)
        if create:
            req.save()
        return req

class UserFactory(factory.Factory):
    FACTORY_FOR = User

    first_name = 'John'
    last_name = 'Doe'
    email = factory.LazyAttribute(lambda a: '{0}.{1}@test.com'.format(a.first_name, a.last_name).lower())
    is_staff = False
    is_active = True
    
    #approval_group = factory.RelatedFactory(GroupFactory)
    approval_group = None
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            
        if create:
            user.save()
        return user
            
    