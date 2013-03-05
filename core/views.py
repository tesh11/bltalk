from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import RequestSite
from django.core.urlresolvers import reverse
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
from core import models


@csrf_exempt
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
        listings = models.get_listing_by_zipcode_sorted_by_amount(settings.DB, session_data['zipcode'], 10)
    else:
        listings = models.get_all_listings_sorted_by_amount(settings.DB, 10)

    return render_to_response('index.html', RequestContext(request, {
        'zipcode_form': zipcode_form,
        'listings': listings,
    }))


@csrf_exempt
def login(request, *args, **kwargs):
    # try to log the user in. if it succeeds, then associate the user with the current session key. otherwise, continue
    response = django_login(request, *args, **kwargs)

    if request.user.is_authenticated():
        # TODO: technically we should delete the anon data
        models.set_session_data(settings.DB, request.user, request.session.session_key, set_zipcode=False)

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

    current_site = RequestSite(request)

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
        listing_form = ListingForm(request.POST)
        if listing_form.is_valid():
            cleaned_data = listing_form.cleaned_data
            models.set_listing(settings.DB, request.user, cleaned_data['title'], cleaned_data['description'],
                               cleaned_data['amount'], cleaned_data['zipcode'])
            return HttpResponseRedirect(reverse('index'))
    else:
        listing_form = ListingForm()

    return render_to_response('new_listing.html', RequestContext(request, {'listing_form': listing_form}))


def setup_test(request, *args, **kwargs):
    # clear out the users, sessiondata and listings
    models.clear_data(settings.DB)

    # create 10 test users
    users = 10 * [None]
    for i in range(1, 11):
        u = u'user%d' % i
        users[i - 1] = models.set_user(settings.DB, u, u)

    # now, create 1mm listings
    # listings = 10000 * [None]
    # for i in range(0, 100):
    #     print ".",
    #     for j in range(0, 10000):
    #         listings[j] = Listing(title=_random_string(), description=_random_zipcode(), amount=random.random() * 100.0,
    #                               zipcode=_random_zipcode(), owner=users[int(random.random() * 10)])
    #     Listing.objects.bulk_create(listings)

    return HttpResponse("OK")
