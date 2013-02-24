from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as django_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from core.forms import ZipcodeForm, ListingForm
from core.models import SessionData, Listing


def index(request, *args, **kwargs):
    # look for session data for the current session or user. if it exists, use it. otherwise, create an object and use
    # that going forward
    if not request.session.session_key:
        request.session.modified = True
        request.session.save()

    if request.user.is_authenticated():
        session_data, created = SessionData.objects.get_or_create(user=request.user)
        if not session_data.session_id:
            session_data.session_id = request.session.session_key
    else:
        session_data, created = SessionData.objects.get_or_create(session_id=request.session.session_key)

    session_data.save(force_update=True)

    if request.method == 'POST':
        zipcode_form = ZipcodeForm(request.POST, instance=session_data)
        if zipcode_form.is_valid():
            zipcode_form.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        zipcode_form = ZipcodeForm(instance=session_data)

    # put together the listings. if there is a zip, filter the values. otherwise, return them all sorted by price
    # ascending
    listings = Listing.objects.all()
    if session_data.zipcode:
        listings = listings.filter(zipcode=session_data.zipcode)
    listings = listings.order_by('amount')

    return render_to_response('index.html', RequestContext(request, {
        'zipcode_form': zipcode_form,
        'listings': listings,
    }))


def login(request, *args, **kwargs):
    # try to log the user in. if it succeeds, then associate the user with the current session key. otherwise, continue
    response = django_login(request, *args, **kwargs)

    if request.user.is_authenticated():
        SessionData.objects.filter(session_id=request.session.session_key).update(user=request.user)

    return response


@login_required
def new_listing(request, *args, **kwargs):
    if request.method == "POST":
        listing = Listing(owner=request.user)
        listing_form = ListingForm(request.POST, instance=listing)
        if listing_form.is_valid():
            listing_form.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        listing_form = ListingForm()

    return render_to_response('new_listing.html', RequestContext(request, {'listing_form': listing_form}))