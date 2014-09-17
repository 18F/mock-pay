from django.http import HttpResponse
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed


def entry(request):
    """Browser is POSTed to here to initiate a payment"""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    elif not request.POST.get('agency_id'):
        return HttpResponseBadRequest('Needs agency_id')
    elif not request.POST.get('agency_tracking_id'):
        return HttpResponseBadRequest('Needs agency_tracking_id')
    else:
        return HttpResponse(str(request.POST))
