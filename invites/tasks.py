from celery import task
from invites.models import User
from django.conf import settings
from urllib2 import urlopen, HTTPError
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile
from django.core.mail import send_mail

@task(ignore_result=True)
def fetch_google_pic(pk):
    user = User.objects.get(pk=pk);
    pic = urlopen(user.google_pic_url)
    pic_file = ContentFile(pic.read())
    user.google_pic.save('pic_%s.jpg' % slugify(user.email), pic_file)
    
@task(ignore_result=True)
def send_email_async(*args, **kwargs):
    send_mail(*args, **kwargs)