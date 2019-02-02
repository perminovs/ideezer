"""
Django settings for root project.

Generated by 'django-admin startproject' using Django 2.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import pathlib
import logging

import environ


PROJECT_DIR = pathlib.Path(__file__).parent
STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_DIR / STATIC_URL

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%frkmb6#d!l*-1mniyc1%(3@d*ujz7tjwd0wexs_rn$ic1f*2$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

HOSTNAME = env('HOSTNAME', default='')
SERVICE_NAME = env('SERVIC_NAME', default='web')

ALLOWED_HOSTS = [SERVICE_NAME, '127.0.0.1', 'localhost']
INTERNAL_IPS = ['127.0.0.1', 'localhost']

LOGIN_URL = '/deezer_auth'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ideezer.apps.IdeezerConfig',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'root.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ideezer.templates.context_processors.deezer_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'root.wsgi.application'


DATABASES = {
    'default': env.db(),
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'general': {
            'format': '[%(asctime)s] <%(levelname)s> %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'general',
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'general',
            'filename': os.path.join(os.getcwd(), 'log.log'),
        },
    },

    'loggers': {
        'ideezer': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        },
        'celery': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
    },
}

AUTHENTICATION_BACKENDS = [
    'ideezer.authbackend.Authbackend',
    'django.contrib.auth.backends.ModelBackend',
]
AUTH_USER_MODEL = 'ideezer.User'

# check Deezer app params
DEEZER_APP_ID = env('DEEZER_APP_ID', default=None)
DEEZER_APP_NAME = env('DEEZER_APP_NAME', default=None)
DEEZER_SECRET_KEY = env('DEEZER_SECRET_KEY', default=None)
DEEZER_BASE_PERMS = env('DEEZER_BASE_PERMS', default='basic_access,email,manage_library')


logger = logging.getLogger(__name__)
for param, name in zip(
    (DEEZER_APP_ID, DEEZER_APP_NAME, DEEZER_SECRET_KEY),
    ('DEEZER_APP_ID', 'DEEZER_APP_NAME', 'DEEZER_SECRET_KEY'),
):
    if not param:
        logger.warning('env var `%s` is not defined', name)

# CELERY STUFF
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='django-db')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

UPLOAD_PATH = env('UPLOAD_PATH', default=None)
