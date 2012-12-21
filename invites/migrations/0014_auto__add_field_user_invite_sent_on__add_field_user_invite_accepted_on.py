# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.invite_sent_on'
        db.add_column('invites_user', 'invite_sent_on',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'User.invite_accepted_on'
        db.add_column('invites_user', 'invite_accepted_on',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.invite_sent_on'
        db.delete_column('invites_user', 'invite_sent_on')

        # Deleting field 'User.invite_accepted_on'
        db.delete_column('invites_user', 'invite_accepted_on')


    models = {
        'holiday_manager.approvalgroup': {
            'Meta': {'object_name': 'ApprovalGroup'},
            'approvers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['invites.User']", 'through': "orm['holiday_manager.ApprovalRule']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.Project']"})
        },
        'holiday_manager.approvalrule': {
            'Meta': {'ordering': "('order',)", 'object_name': 'ApprovalRule'},
            'approver': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['invites.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.ApprovalGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        'holiday_manager.project': {
            'Meta': {'object_name': 'Project'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day_count_reset_date': ('django.db.models.fields.CharField', [], {'default': "'1/1'", 'max_length': '20'}),
            'default_days_off': ('django.db.models.fields.SmallIntegerField', [], {'default': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'default': "'Europe/London'", 'max_length': '100'}),
            'google_calendar_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'plan': ('django.db.models.fields.CharField', [], {'default': "'free'", 'max_length': '20'}),
            'plan_users': ('django.db.models.fields.SmallIntegerField', [], {'default': '3'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '30'}),
            'trial_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'weekly_closure_days': ('holiday_manager.fields.ListField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'invites.user': {
            'Meta': {'unique_together': "(('email', 'project'),)", 'object_name': 'User'},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'approval_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.ApprovalGroup']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'days_off_left': ('django.db.models.fields.SmallIntegerField', [], {'default': '20'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'google_pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'google_pic_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_accepted_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'invite_sent_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_approver': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'paymill_client_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'pending_approvals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.Project']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'Europe/London'", 'max_length': '100'})
        }
    }

    complete_apps = ['invites']