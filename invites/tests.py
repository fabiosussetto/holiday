from django.test import TestCase
from holiday_manager.models import HolidayApproval, HolidayRequest, ApprovalGroup, ApprovalRule, Project
from invites.models import User
from invites.fixtures.factories import (
    UserFactory, GroupFactory, ApprovalRuleFactory, HolidayRequestFactory, ProjectFactory )
import datetime

def reload_entity(obj):
    return obj.__class__.objects.get(pk=obj.pk)

class ApprovalFlowBaseScenario(object):

    def setUp(self):
        self.project = ProjectFactory()
        self.frontend_group = GroupFactory(name='Frontend team', project=self.project)
        self.backend_group = GroupFactory(name='Backend team', project=self.project)
        self.fe_approver_1 = UserFactory(first_name='Mark', last_name='Green', project=self.project)
        self.fe_approver_2 = UserFactory(first_name='Adam', last_name='Red', approval_group=self.frontend_group, project=self.project)
        self.fe_user_1 = UserFactory(first_name='John', last_name='Doe', approval_group=self.frontend_group, project=self.project)
        
        r1 = ApprovalRuleFactory(order=0, group=self.frontend_group, approver=self.fe_approver_1)
        r2 = ApprovalRuleFactory(order=1, group=self.frontend_group, approver=self.fe_approver_2)
        
        self.req = HolidayRequestFactory.build(
            author=self.fe_user_1,
            requested_days_ago=3,
            start_date=datetime.date(2012, 11, 1),
            end_date=datetime.date(2012, 11, 3),
            project=self.project
        )
        

class ApprovalFlowTestCase(ApprovalFlowBaseScenario, TestCase):

    def testSubmitRequest(self):
        
        submitted_req, approval_list = self.req.submit()
        
        initial_days_left = self.fe_user_1.days_off_left
        
        self.fe_approver_1 = reload_entity(self.fe_approver_1)
        self.fe_approver_2 = reload_entity(self.fe_approver_2)
        
        self.assertEqual(self.fe_approver_1.pending_approvals, 1)
        self.assertEqual(self.fe_approver_2.pending_approvals, 0)
        
        approvals_qs = HolidayApproval.objects.filter(request=submitted_req).order_by('order')
        approvals = list(approvals_qs)
        
        self.assertEqual(len(approvals), 2)
        self.assertEqual(approvals[0].status, HolidayApproval.STATUS.pending)
        self.assertEqual(approvals[0].approver, self.fe_approver_1)
        
        self.assertEqual(approvals[1].status, HolidayApproval.STATUS.waiting)
        self.assertEqual(approvals[1].approver, self.fe_approver_2)
        
        self.assertEqual(submitted_req.status, HolidayRequest.STATUS.pending)
        
        approvals[0].approve()
        
        self.fe_approver_1 = reload_entity(self.fe_approver_1)
        self.fe_approver_2 = reload_entity(self.fe_approver_2)
        
        self.assertEqual(self.fe_approver_1.pending_approvals, 0)
        self.assertEqual(self.fe_approver_2.pending_approvals, 1)
        
        self.assertEqual(self.fe_user_1.days_off_left, initial_days_left)
        
        submitted_req = reload_entity(submitted_req)
        
        self.assertEqual(submitted_req.status, HolidayRequest.STATUS.pending)
        
        new_approvals = list(approvals_qs.all())
        self.assertEqual(new_approvals[0].status, HolidayApproval.STATUS.approved)
        self.assertEqual(new_approvals[1].status, HolidayApproval.STATUS.pending)
        
        new_approvals[1].approve()
        
        submitted_req = reload_entity(submitted_req)
        
        self.assertEqual(submitted_req.status, HolidayRequest.STATUS.approved)
        
        self.fe_user_1 = reload_entity(self.fe_user_1)
        
        self.assertEqual(self.fe_user_1.days_off_left, initial_days_left - 2)
        
        
class FirstApprovalRejectTestCase(ApprovalFlowBaseScenario, TestCase):

    def testFirstApproverRejectRequest(self):
        submitted_req, approval_list = self.req.submit()
        
        approvals_qs = HolidayApproval.objects.filter(request=submitted_req).order_by('order')
        approvals = list(approvals_qs)
        
        approvals[0].reject()
        new_approvals = list(approvals_qs.all())
        
        self.assertEqual(new_approvals[0].status, HolidayApproval.STATUS.rejected)
        self.assertEqual(new_approvals[1].status, HolidayApproval.STATUS.pre_rejected)
        
        submitted_req = HolidayRequest.objects.get(pk=submitted_req.pk)
        self.assertEqual(submitted_req.status, HolidayRequest.STATUS.rejected)
        
        
class LastApprovalRejectTestCase(ApprovalFlowBaseScenario, TestCase):

    def testLastApproverRejectRequest(self):
        submitted_req, approval_list = self.req.submit()
        
        approvals_qs = HolidayApproval.objects.filter(request=submitted_req).order_by('order')
        approvals = list(approvals_qs)
        
        approvals[0].approve()
        approvals[1].reject()
        
        submitted_req = HolidayRequest.objects.get(pk=submitted_req.pk)
        self.assertEqual(submitted_req.status, HolidayRequest.STATUS.rejected)
            
        
        
        
        