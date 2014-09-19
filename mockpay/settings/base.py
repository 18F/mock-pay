# Common Django settings
MIDDLEWARE_CLASSES = []
APPEND_SLASH = False
ROOT_URLCONF = "mockpay.urls"
INSTALLED_APPS = [
    "mockpay",
]

# Custom settings,

AGENCY_CONFIG = {}
# Format: {agency_id: {
#   "transaction_url": a_url,       -- initial callback url
#   "collection_results_url": b_url,    --- callback url after completion
#   "success_return_url": c_url,    -- url to redirect browser on success
#   "failure_return_url": d_url,    -- url to redirect browser on failure
#   "allow_amount_change": boolean, -- optional, defaults to False
#   "show_confirmation_screen": boolean, -- optional, default to False
#   "apps": {app_name: {dictionary-of-fields-overriding-above}}}}

FORM_CONFIGS = {}
# We don't know how forms are configured yet, so this is just a best guess.
# Map forms to a list of fields
# Format: {form_id: [{"name": field_name, "status": "editable|locked|hidden"},
#                    ...]}
