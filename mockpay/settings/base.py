# Common Django settings
MIDDLEWARE_CLASSES = []
APPEND_SLASH = False
ROOT_URLCONF = "mockpay.urls"

# Custom settings,

CALLBACK_INFO = {}
# Format: {agency_id: {
#                      app_name: {"form_id": an_int, "url": a_url},
#                      "DEFAULT": {"form_id": an_int, "url": a_url}
#         }}
