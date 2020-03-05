#!/bin/sh
. /srv/django/kululasku/env/bin/activate
/srv/django/kululasku/manage.py send_invoices
/srv/django/kululasku/manage.py send_katre