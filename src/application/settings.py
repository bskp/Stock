"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module, 
           which should be kept out of version control.

"""

import os

from secret_keys import CSRF_SECRET_KEY, SESSION_KEY

# Settings for image uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

SQLALCHEMY_DATABASE_URI = 'sqlite:///../sqlite.db'

DEBUG = True

# Credentials for admin
PASSWORD = '0815'

# Set secret keys for CSRF protection
SECRET_KEY = CSRF_SECRET_KEY
CSRF_SESSION_KEY = SESSION_KEY

CSRF_ENABLED = True

# Flask-DebugToolbar settings
#DEBUG_TB_PROFILER_ENABLED = DEBUG
#DEBUG_TB_INTERCEPT_REDIRECTS = False
