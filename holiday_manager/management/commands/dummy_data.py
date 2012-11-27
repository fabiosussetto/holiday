from django.core.management.base import BaseCommand, CommandError
from holiday_manager import models
from datetime import datetime, date, timedelta
from django.db import transaction
from invites.fixtures import factories
import faker
from faker.generators import name
from holiday_manager import cal
import random

def random_daterange(start, end, mix_length, max_length):
    date_range = list(cal.date_range(start, end))
    while True:
        start_index = random.randint(0, len(date_range))
        end_index = start_index + random.randint(mix_length, max_length)
        if end_index < len(date_range):
            break
    
    return date_range[start_index], date_range[end_index]

class Command(BaseCommand):
    help = "Create dummy data"
    
    @transaction.commit_on_success
    def handle(self, *args, **options):
        
        project = factories.ProjectFactory(name='Dummy Project', slug='dummy-project')
        admin = factories.UserFactory(first_name='Fabio', last_name='Sussetto', password='123456', project=project, is_superuser=True)
        
        t1 = factories.GroupFactory(name='Frontend Team', project=project)
        t2 = factories.GroupFactory(name='Backend Team', project=project)
        t3 = factories.GroupFactory(name='Analytics Team', project=project)
        
        approver1 = factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                email=faker.internet.email(),
                password='123456',
                project=project,
                is_superuser=False,
                approval_group=t1
            )
        
        approver2 = factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                password='123456',
                email=faker.internet.email(),
                project=project,
                is_superuser=False,
                approval_group=t1
            )
        
        approver3 = factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                password='123456',
                email=faker.internet.email(),
                project=project,
                is_superuser=False,
                approval_group=t1
            )
        
        approver4 = factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                password='123456',
                email=faker.internet.email(),
                project=project,
                is_superuser=False,
                approval_group=t1
            )
        
        rule1 = factories.ApprovalRuleFactory(
            group=t1,
            order=0,
            approver=approver1
        )
        rule2 = factories.ApprovalRuleFactory(
            group=t1,
            order=1,
            approver=approver2
        )

        rule3 = factories.ApprovalRuleFactory(
            group=t2,
            order=0,
            approver=approver3
        )
        
        rule4 = factories.ApprovalRuleFactory(
            group=t3,
            order=0,
            approver=approver4
        )
        
        t1_users = t2_users = t3_users = []
                
        for i in range(0, 25):
            t1_users.append(factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                email=faker.internet.email(),
                password='123456',
                project=project,
                is_superuser=False,
                approval_group=t1
            ))
        
        for i in range(0, 15):
            t2_users.append(factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                password='123456',
                project=project,
                is_superuser=False,
                approval_group=t2
            ))
            
        for i in range(0, 10):
            t3_users.append(factories.UserFactory(
                first_name=name.first_name(),
                last_name=name.last_name(),
                password='123456',
                project=project,
                is_superuser=False,
                approval_group=t3
            ))
            
        distribution = ((t1_users, 20), (t2_users, 10), (t3_users, 10))
            
        for users, num in distribution:
            for i in range(0, num):
                start, end = random_daterange(date(2012, 11, 22), date(2012, 12, 22), 1, 7)
                
                r = factories.HolidayRequestFactory.build(
                    requested_on=start - timedelta(days=random.randint(2, 15)),
                    start_date=start,
                    end_date=end,
                    author=random.choice(users),
                    project=project
                )
                
                r, approvals = r.submit()
                if random.randint(0, 1):
                    for approval in approvals:
                        approval.approve()
        
            
        