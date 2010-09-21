from django.conf.urls.defaults import *
from django.contrib import admin
from achewood2.admin import adminsite

#adminsite.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^achewood2/', include('achewood2.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(adminsite.urls)),
)
