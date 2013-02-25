from django.forms import Form, CharField, FloatField


class ZipcodeForm(Form):
    zipcode = CharField(max_length=5, required=False)


class ListingForm(Form):
    title = CharField(max_length=255)
    description = CharField()
    amount = FloatField()
    zipcode = CharField(max_length=5)