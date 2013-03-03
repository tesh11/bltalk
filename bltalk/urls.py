from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
                       # Examples:
                       url(r'^$', 'core.views.index', name='blindex'),
                       url(r'^login/$', 'core.views.login', {'template_name': 'login.html'}, name='login'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
                       url(r'^listing/new/$', 'core.views.new_listing', name='new_listing'),
                       url(r'^setup_test/$', 'core.views.setup_test', name='setup_test'),

                       url(r'^mongonaut/', include('mongonaut.urls')),
)
