import locale

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'postgres',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'postgres',
        #'PASSWORD': 'Ah6fDSBie0lfFICIBJN9',
        'HOST': 'db',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '5432'                   # Set to empty string for default.
    }
}

SECRET_KEY='CHANGE_ME_PLEASE'
ROOT_URLCONF = 'expenses.urls'


EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'aucor'
EMAIL_HOST_PASSWORD = 'roi 24 paketti'
EMAIL_PORT = 25
EMAIL_USE_TLS = True
locale.setlocale(locale.LC_ALL, 'fi_FI.UTF-8')

#locale.setlocale(locale.LC_ALL, 'fi_FI')

LOGGING = {
  'version': 1,
  'disable_existing_loggers': False,
  'handlers': {
    'null': {
      'level': 'DEBUG',
      'class': 'logging.NullHandler',
    },
  },
  'loggers': {
    'django.security.DisallowedHost': {
      'handlers': ['null'],
      'propagate': False,
    },
  },
}
