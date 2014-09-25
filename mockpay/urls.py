from django.conf.urls import patterns, url

from mockpay import views


urlpatterns = patterns(
    '',
    url(r'^paygov/OCIServlet$', views.entry, name='entry'),
    url(r'^paygov/redirect$', views.exit_redirect, name='redirect'),
)
