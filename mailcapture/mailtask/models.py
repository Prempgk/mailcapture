import datetime

from django.db import models
from django_mysql.models import ListTextField


# Create your models here.

class MailDetails(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.TextField(null=True, blank=True)
    from_mail = models.EmailField(null=False, blank=False)
    text_body = models.CharField(max_length=2000, null=True, blank=True)
    html_body = models.CharField(max_length=2000, null=True, blank=True)
    attachments = models.JSONField()
    received_at = models.DateTimeField(null=False, blank=False)


