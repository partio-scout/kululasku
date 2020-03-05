#!/bin/sh
. /srv/django/kululasku/env/bin/activate
/srv/django/kululasku/manage.py send_queued_messages
