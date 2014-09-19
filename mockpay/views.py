from copy import deepcopy

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.shortcuts import render
import requests

from mockpay.access_settings import clean_response, clean_callback
from mockpay.access_settings import lookup_config


@require_POST
def entry(request):
    """Browser is POSTed to here to initiate a payment"""
    agency_id = request.POST.get('agency_id')
    app_name = request.POST.get('app_name')
    if not agency_id:
        return HttpResponseBadRequest('Needs agency_id')
    elif not request.POST.get('agency_tracking_id'):
        return HttpResponseBadRequest('Needs agency_tracking_id')
    else:
        url = lookup_config("transaction_url", agency_id, app_name)
        if not url:
            return HttpResponseBadRequest(
                'agency_id + app_name cannot be found in settings')
        else:
            data = {'agency_id': agency_id,
                    'agency_tracking_id': request.POST['agency_tracking_id']}
            agency_response = requests.post(url, data=data)
            agency_response = agency_response_to_dict(agency_response.text)
            if isinstance(agency_response, dict):
                agency_response = clean_response(agency_response)
            if isinstance(agency_response, str):
                return HttpResponseBadRequest(agency_response)
            else:
                return generate_form(request, agency_id, app_name,
                                     agency_response)


def generate_form(request, agency_id, app_name, cleaned_params):
    """Generate an HTML form of payment/user information. To do this, lookup
    the form configuration in the settings."""
    form_id = cleaned_params['form_id']
    if form_id not in settings.FORM_CONFIGS:
        return HttpResponseBadRequest("could not find form " + form_id)
    else:
        form = deepcopy(settings.FORM_CONFIGS[form_id])
        #   always include these system fields
        form.append({'name': 'agency_id', 'status': 'hidden',
                     'value': agency_id})
        if app_name is not None:
            form.append({'name': 'app_name', 'status': 'hidden',
                         'value': app_name})
        for field in ('agency_tracking_id', 'collection_results_url',
                      'success_return_url', 'failure_return_url'):
            if field not in form and field in cleaned_params:
                form.append({'name': field, 'status': 'hidden'})

        #   insert values given by the callback url
        for field in form:
            if field["name"] in cleaned_params:
                field["value"] = cleaned_params[field["name"]]
        #   @todo: account for allow_amount_change and
        #   show_confirmation_screen
        return render(request, "mockpay/form.html", {"form": form})


def agency_response_to_dict(response_str):
    """Agency responses contain many key-value pairs. Turn them into a
    dict."""
    if response_str[:1] == "<":
        #   @TODO
        return "mock-pay does not currently support xml"
    else:
        mapping = {}
        for line in response_str.splitlines():
            pair = line.split("=")
            key = pair[0]
            if key in mapping:
                return "duplicate key: " + key
            if len(pair) == 1 or not pair[1].strip():
                return "no value for key: " + key
            else:
                mapping[key] = pair[1]
        return mapping


@require_POST
def exit_redirect(request):
    """Browser POST to here with their credit card info. Redirect as needed"""
    agency_id = request.POST['agency_id']
    app_name = request.POST.get('app_name')
    canceled = request.POST.get('cancel')
    agency_response = send_status_to_agency(request, agency_id, app_name)
    if (not isinstance(agency_response, dict)
            or agency_response.get('response_message') != 'OK'):
        canceled = True
    if canceled:
        url_key = 'failure_return_url'
    else:
        url_key = 'success_return_url'
    redirect_to = lookup_config(url_key, agency_id, app_name,
                                request.POST)
    return render(request, "mockpay/redirect.html", {
        "agency_id": agency_id, "redirect_url": redirect_to,
        "agency_tracking_id": request.POST.get('agency_tracking_id')})


def send_status_to_agency(request, agency_id, app_name):
    """As part of the exit redirect, we need to tell the agency what the
    outcome was."""
    canceled = request.POST.get('cancel')
    callback_data = deepcopy(request.POST)
    if canceled:
        callback_data['payment_status'] = 'Canceled'
    else:
        callback_data['payment_status'] = 'Success'
    callback_data = clean_callback(callback_data)
    callback_url = lookup_config("collection_results_url", agency_id,
                                 app_name, request.POST)
    agency_response = requests.post(callback_url, data=callback_data)
    return agency_response_to_dict(agency_response.text)
