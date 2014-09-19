from copy import deepcopy

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render
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
        url = lookup_callback_url(request.POST['agency_id'],
                                  request.POST.get('app_name'))
        if not url:
            return HttpResponseBadRequest(
                'agency_id + app_name cannot be found in settings')
        else:
            data = {'agency_id': request.POST['agency_id'],
                    'agency_tracking_id': request.POST['agency_tracking_id']}
            agency_response = requests.post(url, data=data)
            agency_response = clean_agency_response(agency_response.text)
            if isinstance(agency_response, str):
                return HttpResponseBadRequest(agency_response)
            else:
                return generate_form(request, agency_response)


def lookup_callback_url(agency_id, app_name=None):
    """Callbacks (from mockpay to the client app) are configured in the
    settings file. An app_name of None indicates that we should use the
    "DEFAULT" key"""
    if agency_id in settings.CALLBACK_URLS:
        if app_name is None:
            app_name = 'DEFAULT'
        if app_name in settings.CALLBACK_URLS[agency_id]:
            return settings.CALLBACK_URLS[agency_id][app_name]


def clean_agency_response(response_str):
    """The agency's response contains many key-value pairs. Turn them into a
    dict and validate the result or return an error string"""
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

        required = ['protocol_version', 'response_message', 'action',
                    'form_id', 'agency_tracking_id']
        # @todo: payment_type (required if account data is presented)
        optional = [
            'payment_type', 'collection_results_url', 'success_return_url',
            'failure_return_url', 'show_confirmation_screen',
            'allow_account_data_change', 'allow_amount_change',
            'allow_date_change', 'allow_recurring_data_change',
            'return_account_id_data', 'agency_memo', 'payment_amount',
            'credit_card_transaction_type', 'paygov_tracking_id', 'order_id',
            'order_tax_amount', 'order_level3_data', 'payment_date',
            'recur_frequency', 'recur_count', 'payer_name', 'bank_name',
            'bank_account_type', 'bank_account_number', 'check_type',
            'check_micr_line', 'credit_card_number',
            'credit_card_expiration_date', 'card_security_code',
            'billing_address', 'billing_city', 'billing_state', 'billing_zip',
            'custom_field_1', 'custom_field_2', 'custom_field_3',
            'custom_field_4', 'custom_field_5', 'custom_field_6',
            'custom_field_7', 'custom_field_8', 'custom_field_9',
            'custom_field_10', 'custom_field_11', 'custom_field_12']

        for key in required:
            if not mapping.get(key):
                return "missing required key: " + key
        for key in mapping:
            if key not in required and key not in optional:
                return "unknown key: " + key

        return mapping


def generate_form(request, cleaned_params):
    """Generate an HTML form of payment/user information. To do this, lookup
    the form configuration in the settings."""
    form_id = cleaned_params['form_id']
    if form_id not in settings.FORM_CONFIGS:
        return HttpResponseBadRequest("could not find form " + form_id)
    else:
        form = deepcopy(settings.FORM_CONFIGS[form_id])
        for field in form:
            if field["name"] in cleaned_params:
                field["value"] = cleaned_params[field["name"]]
        return render(request, "mockpay/form.html", {"form": form})
