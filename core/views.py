from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as django_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from core.forms import ZipcodeForm, ListingForm
from core import models


def index(request, *args, **kwargs):
    # look for session data for the current session or user. if it exists, use it. otherwise, create an object and use
    # that going forward
    if not request.session.session_key:
        request.session.modified = True
        request.session.save()

    if request.user.is_authenticated():
        models.set_session_data(settings.DB, request.user, request.session.session_key, set_zipcode=False)
        session_data = models.get_session_data_by_user(settings.DB, request.user)
    else:
        models.set_session_data(settings.DB, None, request.session.session_key, set_zipcode=False)
        session_data = models.get_session_data_by_session_id(settings.DB, request.session.session_key)

    if request.method == 'POST':
        zipcode_form = ZipcodeForm(request.POST)
        if zipcode_form.is_valid():
            cleaned_data = zipcode_form.cleaned_data
            if request.user.is_authenticated():
                models.set_session_data(settings.DB, request.user, request.session.session_key, cleaned_data['zipcode'])
            else:
                models.set_session_data(settings.DB, None, request.session.session_key, cleaned_data['zipcode'])
            return HttpResponseRedirect(reverse('index'))
    else:
        zipcode = session_data['zipcode']
        zipcode_form = ZipcodeForm({'zipcode': zipcode if zipcode else ''})

    # put together the listings. if there is a zip, filter the values. otherwise, return them all sorted by price
    # ascending
    if session_data['zipcode']:
        listings = models.get_listing_by_zipcode(settings.DB, session_data['zipcode'])
    else:
        listings = models.get_all_listings(settings.DB)
    listings.sort(key=lambda x: float(x['amount']))

    return render_to_response('index.html', RequestContext(request, {
        'zipcode_form': zipcode_form,
        'listings': listings,
    }))


def login(request, *args, **kwargs):
    # try to log the user in. if it succeeds, then associate the user with the current session key. otherwise, continue
    response = django_login(request, *args, **kwargs)

    if request.user.is_authenticated():
        # TODO: technically we should delete the anon data
        models.set_session_data(settings.DB, request.user, request.session.session_key, set_zipcode=False)

    return response


@login_required
def new_listing(request, *args, **kwargs):
    if request.method == "POST":
        listing_form = ListingForm(request.POST)
        if listing_form.is_valid():
            cleaned_data = listing_form.cleaned_data
            models.set_listing(settings.DB, request.user, cleaned_data['title'], cleaned_data['description'],
                               cleaned_data['amount'], cleaned_data['zipcode'])
            return HttpResponseRedirect(reverse('index'))
    else:
        listing_form = ListingForm()

    return render_to_response('new_listing.html', RequestContext(request, {'listing_form': listing_form}))