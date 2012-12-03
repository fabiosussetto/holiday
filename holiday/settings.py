# Django settings for holiday2 project.
import os
import django
import sys

DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

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

if 'test' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}
    
SOUTH_TESTS_MIGRATE = False
    
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3(!lv%mxga^*wj@+7qs#2!-9r+#meyk-ddb8e#hgw1@0v&amp;4s2i'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'holiday_manager.middleware.TimezoneMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'linaro_django_pagination.middleware.PaginationMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    #'social_auth.context_processors.social_auth_by_name_backends',
    'social_auth.context_processors.social_auth_backends',
    #'social_auth.context_processors.social_auth_by_type_backends',
    'social_auth.context_processors.social_auth_login_redirect',
    'holiday_manager.context_processors.django_settings',
    'holiday_manager.context_processors.ajax_partials'
)

ROOT_URLCONF = 'holiday.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'holiday.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'social_auth',
    'debug_toolbar',
    'easy_thumbnails',
    'paypal.standard.ipn',
    'linaro_django_pagination',
    'invites',
    'holiday_manager',
    'datafilters',
    'django.contrib.webdesign'
)

AUTHENTICATION_BACKENDS = (
    #'social_auth.backends.google.GoogleOAuthBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    #'social_auth.backends.google.GoogleBackend',
    #'social_auth.backends.OpenIDBackend',
    #'django.contrib.auth.backends.ModelBackend',
    'holiday.auth_backends.CustomUserModelBackend',
)

GOOGLE_CONSUMER_KEY          = ''
GOOGLE_CONSUMER_SECRET       = ''
GOOGLE_OAUTH2_CLIENT_ID      = '537598744846.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET  = 'fqQz3JbfS-wGvJi4Z5yP-HIA'

GOOGLE_API_KEY = 'AIzaSyDymz8SMM1XC_fnxV_gLd6eozd2nNyRsTg'

LOGIN_REDIRECT_URL = '/'

CUSTOM_USER_MODEL = 'invites.User'

SOCIAL_AUTH_COMPLETE_URL_NAME  = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'

SOCIAL_AUTH_USER_MODEL = 'invites.User'

SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'holiday_manager.social_auth_pipeline.user_association_not_found',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details'
)

THUMBNAIL_ALIASES = {
    '': {
        'profile_pic': {'size': (150, 150), 'crop': 'smart'},
        'avatar': {'size': (30, 30), 'crop': 'smart'},
        'home': {'size': (50, 50), 'crop': 'smart'},
    },
}

AWS_ACCESS_KEY_ID = "AKIAI3PEKEUGM7S6RIWQ"
AWS_SECRET_ACCESS_KEY = "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"

AWS_STORAGE_BUCKET_NAME = "holiday-test"

AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False

THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

THUMBNAIL_DEBUG = True

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ACCOUNT_ACTIVATION_DAYS = 5
DEFAULT_FROM_EMAIL = 'test@test.com'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

#INTERNAL_IPS = ('127.0.0.1',)
INTERNAL_IPS = ()


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

GOOGLE_OAUTH_EXTRA_SCOPE = ['https://www.google.com/m8/feeds', 'https://www.googleapis.com/auth/calendar']
GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'access_type': 'offline'}
SOCIAL_AUTH_EXTRA_DATA = True
SOCIAL_AUTH_SESSION_EXPIRATION = False

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: '',
    messages.ERROR: 'alert-error'
}

PAYPAL_RECEIVER_EMAIL = "h1_1352217439_biz@gmail.com"
PAYPAL_TEST = True

# Pricing settings
def _price_function(user_num):
    if user_num <= 10:
        return 5.00
    elif user_num > 30 and user_num <= 50:
        return 4.00
    else:
        return 3.00
    

PRICE_PER_USERS_FUNC = _price_function

TRIAL_PERIOD_DAYS = 15

PAYMILL_PUBLIC_TEST_KEY = '86700143132d486485024c4b2b6e5648'
PAYMILL_PRIVATE_TEST_KEY = '06919cb9f02d8f0c3d1d645c4b4ff373'

PAYMILL_PLAN_SMALL_ID = 'offer_1b37112588ca9c4333dd'

DATE_INPUT_FORMATS = ('%d/%m/%Y',)

THUMBNAIL_ALIASES = {
    'invites.User.google_pic': {
        'thumb': {'size': (40, 40), 'crop': 'smart'},
    },
}