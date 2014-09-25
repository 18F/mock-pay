from django.conf import settings


def lookup_config(key, agency_id, app_name=None, req_config=None):
    """Per-request configurations override app-level configurations, which, in
    turn, override Agency-level configurations If app_name is None, rely on
    agency information"""
    if req_config is None:
        req_config = {}
    config = settings.AGENCY_CONFIG
    if key in req_config:
        return req_config[key]
    if agency_id in config:
        if app_name is not None:
            if app_name not in config[agency_id]["apps"]:
                return None     # No such app
            if key in config[agency_id]["apps"][app_name]:
                # Use app config
                return config[agency_id]["apps"][app_name][key]
        # Default to agency-wide config
        return config[agency_id].get(key)


def validate(data_dict, required, optional, filter_unknown_fields=False):
    """Make sure all required fields are present and all other fields are
    optional. If an unknown field is found and filter_unknown_fields is False,
    return an error. Otherwise, just filter the field out."""
    final = {}
    for key in required:
        if not data_dict.get(key):
            return "missing required key: " + key
    for key in data_dict:
        if key in required or key in optional:
            final[key] = data_dict[key]
        elif not filter_unknown_fields:
            return "unknown key: " + key

    return final


def clean_response(data_dict):
    """Validate based on the initial agency response, i.e. "what information
    have you already collected?" """
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
    return validate(data_dict, required, optional)


def clean_callback(data_dict):
    """Validate input provided by the credit card form; this will be passed to
    the agency callback"""
    required = ['agency_tracking_id', 'payment_status']
    # @todo payment_type (required if account data is presented)
    optional = [
        'agency_id', 'error_message', 'error_detail', 'last_submission_time',
        'agency_memo', 'app_name', 'paygov_tracking_id',
        'return_account_id_data', 'account_id_data', 'payment_amount',
        'payment_date', 'submitted_on', 'recur_frequency', 'recur_count',
        'approval_code', 'avs_response_code', 'payment_type', 'payer_name',
        'payer_address', 'payer_zip', 'bank_name', 'bank_account_type',
        'check_type', 'custom_field_1', 'custom_field_2', 'custom_field_3',
        'custom_field_4', 'custom_field_5', 'custom_field_6',
        'custom_field_7', 'custom_field_8', 'custom_field_9',
        'custom_field_10', 'custom_field_11', 'custom_field_12', 'sec_code',
    ]
    return validate(data_dict, required, optional, filter_unknown_fields=True)
