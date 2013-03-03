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
from mongoengine.django.auth import User

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
        session_data, created = SessionData.objects.get_or_create(user=request.user, auto_save=False)
        if not session_data.session_id:
            session_data.session_id = request.session.session_key
    else:
        session_data, created = SessionData.objects.get_or_create(session_id=request.session.session_key)

    session_data.save()

    if request.method == 'POST':
        zipcode_form = ZipcodeForm(request.POST)
        if zipcode_form.is_valid():
            cleaned_data = zipcode_form.cleaned_data
            session_data.zipcode = cleaned_data['zipcode']
            session_data.save()
            return HttpResponseRedirect(reverse('blindex'))
    else:
        zipcode_form = ZipcodeForm(session_data.to_mongo())

    # put together the listings. if there is a zip, filter the values. otherwise, return them all sorted by price
    # ascending
    listings = Listing.objects.all()
    if session_data.zipcode:
        listings = listings.filter(zipcode=session_data.zipcode)
    listings = listings.order_by('amount').select_related()[:10]

    return render_to_response('index.html', RequestContext(request, {
        'zipcode_form': zipcode_form,
        'listings': listings,
    }))


@csrf_exempt
def login(request, *args, **kwargs):
    # try to log the user in. if it succeeds, then associate the user with the current session key. otherwise, continue
    response = django_login(request, *args, **kwargs)

    if request.user.is_authenticated():
        SessionData.objects.filter(session_id=request.session.session_key).update(set__user=request.user)

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
        listing = Listing(owner=request.user)
        listing_form = ListingForm(request.POST)
        if listing_form.is_valid():
            cleaned_data = listing_form.cleaned_data
            listing.title = cleaned_data['title']
            listing.description = cleaned_data['description']
            listing.amount = cleaned_data['amount']
            listing.zipcode = cleaned_data['zipcode']
            listing.save()
            return HttpResponseRedirect(reverse('blindex'))
    else:
        listing_form = ListingForm()

    return render_to_response('new_listing.html', RequestContext(request, {'listing_form': listing_form}))


def setup_test(request, *args, **kwargs):
    # clear out the users, sessiondata and listings
    Listing.objects.delete()
    SessionData.objects.delete()
    User.objects.filter(username__ne='admin').delete()

    # create 10 test users
    users = 10 * [None]
    for i in range(1, 11):
        u = 'user%d' % i
        users[i - 1] = User.create_user(u, u, None)

    # now, create 1mm listings
    # listings = 10000 * [None]
    # for i in range(0, 100):
    #     print ".",
    #     for j in range(0, 10000):
    #         listings[j] = Listing(title=_random_string(), description=_random_zipcode(), amount=random.random() * 100.0,
    #                               zipcode=_random_zipcode(), owner=users[int(random.random() * 10)])
    #     Listing.objects.bulk_create(listings)

    return HttpResponse("OK")
