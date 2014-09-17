from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
import requests


def entry(request):
    """Browser is POSTed to here to initiate a payment"""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    elif not request.POST.get('agency_id'):
        return HttpResponseBadRequest('Needs agency_id')
    elif not request.POST.get('agency_tracking_id'):
        return HttpResponseBadRequest('Needs agency_tracking_id')
    else:
        callback_info = lookup_callback_info(request.POST['agency_id'],
                                             request.POST.get('app_name'))
        if not callback_info:
            return HttpResponseBadRequest(
                'agency_id + app_name cannot be found in settings')
        else:
            data = {'agency_id': request.POST['agency_id'],
                    'agency_tracking_id': request.POST['agency_tracking_id']}
            agency_response = requests.post(callback_info['url'], data=data)
            return HttpResponse(str(agency_response))


def lookup_callback_info(agency_id, app_name=None):
    """Callbacks (from mockpay to the client app) are configured in the
    settings file. Look up the callback config. An app_name of None indicates
    that we should use the "DEFAULT" key"""
    if agency_id in settings.CALLBACK_INFO:
        if not app_name:
            app_name = 'DEFAULT'
        if app_name in settings.CALLBACK_INFO[agency_id]:
            return settings.CALLBACK_INFO[agency_id][app_name]
