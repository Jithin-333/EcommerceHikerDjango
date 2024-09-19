"""
Django settings for hiker project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ypu&qnops5rhf9r&xeiydsw2q2-rbl^hz47rm(&)i2@n8poo7o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['13.49.64.213', 'localhost', 'hikercart.shop', 'www.hikercart.shop','127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'user',
    'products.apps.ProductsConfig',
    'adminapp.apps.AdminappConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'chartjs',
    'storages',
    'whitenoise.runserver_nostatic',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'hiker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['TEMPLATES/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'user.utils.context_processors.cart_wishlist_counts',  # Add this line
            ],
        },
    },
]


WSGI_APPLICATION = 'hiker.wsgi.application'

AUTH_USER_MODEL = 'adminapp.CustomUser'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hiker',
        'USER': 'postgres',
        'PASSWORD': 'jithins',
        'HOST': 'localhost',
        'PORT': '5433'
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'hikerdatabase',
#         'USER': 'hikerpostgres',
#         'PASSWORD': 'Jithins123#',
#         'HOST': 'hiker-database.cjgc6gok2bb5.eu-north-1.rds.amazonaws.com',
#         'PORT': '5432',
#     }
# }



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'

# Specify the static directories for each app
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'adminapp/static'),
    os.path.join(BASE_DIR, 'hiker/static'),
]



STATIC_ROOT = BASE_DIR / 'staticfiles'


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py

#image uploadss----

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'adminapp/uploads')


# allaouth

AUTHENTICATION_BACKENDS = [
    
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',

]
SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
# LOGIN_REDIRECT_URL = 'https://hikercart.shop'
LOGIN_REDIRECT_URL = 'http://127.0.0.1:8000/'

SOCIALACCOUNT_ADAPTER = 'adminapp.adapters.CustomSocialAccountAdapter'


RAZORPAY_API_KEY = config('API_KEY')
RAZORPAY_API_SECRET  = config('API_SECRET')


# =========aws=============

# AWS_ACCESS_KEY_ID = 'AKIAQE3ROL3BV7V2IFRK '
# AWS_SECRET_ACCESS_KEY = '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'
# AWS_STORAGE_BUCKET_NAME = 'hikerdatabase'
# AWS_S3_SIGNATURE_NAME = 's3v4',
# AWS_S3_REGION_NAME = 'eu-north-1'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL =  None
# AWS_S3_VERIFY = True
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'