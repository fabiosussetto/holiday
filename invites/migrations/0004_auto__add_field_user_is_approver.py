# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.is_approver'
        db.add_column('invites_user', 'is_approver',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.is_approver'
        db.delete_column('invites_user', 'is_approver')


    models = {
        'holiday_manager.approvalgroup': {
            'Meta': {'object_name': 'ApprovalGroup'},
            'approvers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['invites.User']", 'through': "orm['holiday_manager.ApprovalRule']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'holiday_manager.approvalrule': {
            'Meta': {'ordering': "('order',)", 'object_name': 'ApprovalRule'},
            'approver': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['invites.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.ApprovalGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        'invites.user': {
            'Meta': {'object_name': 'User'},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'approval_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['holiday_manager.ApprovalGroup']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'google_pic_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_approver': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['invites']