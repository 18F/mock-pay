# Common Django settings
MIDDLEWARE_CLASSES = []
APPEND_SLASH = False
ROOT_URLCONF = "mockpay.urls"
INSTALLED_APPS = [
    "mockpay",
]

# Custom settings,

CALLBACK_URLS = {}
# Format: {agency_id: {app_name: a_url,
#                      "DEFAULT": a_default_url
#         }}

FORM_CONFIGS = {}
# We don't know how forms are configured yet, so this is just a best guess.
# Map forms to a list of fields
# Format: {form_id: [{"name": field_name, "status": "editable|locked|hidden"},
#                    ...]}
