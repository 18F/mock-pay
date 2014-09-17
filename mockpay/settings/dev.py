from .base import *

DEBUG = True

try:
    from .local_settings import *
except ImportError:
    # Create a random secret key
    from django.utils.crypto import get_random_string
    SECRET_KEY = get_random_string(50)
