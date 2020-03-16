#!/bin/sh
pwd
#. /srv/django/kululasku/env/bin/activate
python manage.py send_invoices
python manage.py send_katre