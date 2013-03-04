import datetime
from mongoengine import Document, ReferenceField, StringField, DateTimeField, FloatField
from mongoengine.django.auth import User


class SessionData(Document):
    user = ReferenceField(User, required=False)
    session_id = StringField(max_length=255, unique=True)
    last_update_timestamp = DateTimeField(default=datetime.datetime.now)

    zipcode = StringField(max_length=5, required=False)

    meta = {
        'indexes': ['user', ]
    }


class Listing(Document):
    owner = ReferenceField(User)
    title = StringField(max_length=255)
    description = StringField()
    amount = FloatField()
    zipcode = StringField(max_length=5)

    meta = {
        'indexes': ['owner', 'zipcode', 'amount']
    }