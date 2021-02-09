import os

from distutils.util import strtobool

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'dangobot.core',
    'dangobot.admin',
    'dangobot.management',
    'dangobot.commands',
    'dangobot.dnd',
]

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'dangobot'),
        'USER': os.getenv('DATABASE_USER', 'dangobot'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Bot settings

COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
DESCRIPTION = os.getenv('DESCRIPTION', 'witty tagline')

BOT_TOKEN = os.environ['BOT_TOKEN']

OWNER_ID = os.getenv('OWNER_ID', None)

# Set this to True and set the your user ID above
# to get notified in DMs about any exceptions that
# occur.
SEND_ERRORS = bool(strtobool(os.getenv('SEND_ERRORS', 'True')))

# Used by the !about command, changing them manually will cause the
# version/date reported there to change
BUILD_VERSION = os.getenv('BUILD_VERSION', None)
BUILD_DATE = os.getenv('BUILD_DATE', None)
