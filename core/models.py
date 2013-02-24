from django.contrib.auth.models import User
from django.db import models


class SessionData(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    session_id = models.CharField(max_length=255, unique=True)
    last_update_timestamp = models.DateTimeField(auto_now=True)

    zipcode = models.CharField(max_length=5, blank=True, null=True)


class Listing(models.Model):
    owner = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.FloatField()
    zipcode = models.CharField(max_length=5, db_index=True)