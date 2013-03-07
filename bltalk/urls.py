from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       url(r'^$', 'core.views.index', name='index'),
                       url(r'^login/$', 'core.views.login', {'template_name': 'login.html'}, name='login'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
                       url(r'^listing/new/$', 'core.views.new_listing', name='new_listing'),
                       url(r'^setup_test/$', 'core.views.setup_test', name='setup_test'),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),
)
