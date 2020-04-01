#!/bin/sh

echo localsettings
ln -s /etc/nginx/sites-available/django_local_nginx.conf /etc/nginx/sites-enabled

python manage.py migrate --fake-initial
python manage.py collectstatic --no-input

mkdir /logs
touch /logs/gunicorn.log
touch /logs/access.log
tail -n 0 -f /logs/*.log /var/log/nginx/*.log &


echo Starting Gunicorn.
exec gunicorn expenses.wsgi \
    --name src \
    --bind unix:django_app.sock \
    --workers 1 \
    --log-level=info \
    --log-file=/logs/gunicorn.log \
    --access-logfile=/logs/access.log \
    --reload &

#exec python manage.py runserver

echo Starting nginx.
exec service nginx start

exec "$@"