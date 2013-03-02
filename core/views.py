from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import login as auth_login

from core.forms import ZipcodeForm, ListingForm
from core.models import SessionData, Listing


@csrf_exempt
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
    listings = listings.select_related('user').order_by('amount')

    return render_to_response('index.html', RequestContext(request, {
        'zipcode_form': zipcode_form,
        'listings': listings,
    }))


@csrf_exempt
def login(request, *args, **kwargs):
    # try to log the user in. if it succeeds, then associate the user with the current session key. otherwise, continue
    response = django_login(request, *args, **kwargs)

    if request.user.is_authenticated():
        SessionData.objects.filter(session_id=request.session.session_key).update(user=request.user)

    return response


@sensitive_post_parameters()
@never_cache
def django_login(request, template_name='registration/login.html',
                 redirect_field_name=REDIRECT_FIELD_NAME,
                 authentication_form=AuthenticationForm,
                 current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


@csrf_exempt
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


def setup_test(request, *args, **kwargs):
    # clear out the users, sessiondata and listings
    cursor = connection.cursor()
    cursor.execute('truncate table core_listing')
    cursor.execute('truncate table core_sessiondata')
    transaction.commit_unless_managed()

    User.objects.exclude(username='admin').delete()

    # create 10 test users
    for i in range(1, 11):
        u = 'user%d' % i
        User.objects.create_user(u, None, u)

    return HttpResponse("OK")