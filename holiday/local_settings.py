ENV = 'local'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'NAME': 'holiday',                      # Or path to database file if using sqlite3.
        'NAME': 'holiday_dummy',                      # Or path to database file if using sqlite3.
        #'NAME': 'holiday',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': 'root',                  # Not used with sqlite3.
        'HOST': '/Applications/MAMP/tmp/mysql/mysql.sock', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

GOOGLE_CONSUMER_KEY          = ''
GOOGLE_CONSUMER_SECRET       = ''
GOOGLE_OAUTH2_CLIENT_ID      = '537598744846.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET  = 'fqQz3JbfS-wGvJi4Z5yP-HIA'

GOOGLE_API_KEY = 'AIzaSyDymz8SMM1XC_fnxV_gLd6eozd2nNyRsTg'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

PAYMILL_PUBLIC_TEST_KEY = '86700143132d486485024c4b2b6e5648'
PAYMILL_PRIVATE_TEST_KEY = '06919cb9f02d8f0c3d1d645c4b4ff373'

PAYMILL_PLAN_SMALL_ID = 'offer_1b37112588ca9c4333dd'