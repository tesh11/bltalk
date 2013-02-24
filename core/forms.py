from django.forms import ModelForm
from core.models import SessionData, Listing


class ZipcodeForm(ModelForm):
    class Meta:
        model = SessionData
        fields = ('zipcode', )


class ListingForm(ModelForm):
    class Meta:
        model = Listing
        fields = ('title', 'description', 'amount', 'zipcode')