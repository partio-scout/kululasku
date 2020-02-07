#!/bin/sh

# if [ "$DJANGO_ENV" = "production" ]
# then
#   echo prodsettings
#   cp src/prodsettings.py src/settings.py
#   ln -s /etc/nginx/sites-available/django_production_nginx.conf /etc/nginx/sites-enabled

# else
echo localsettings
#cp src/localsettings.py src/settings.py
ln -s /etc/nginx/sites-available/django_local_nginx.conf /etc/nginx/sites-enabled

#rm /etc/nginx/sites-available/django_production_nginx.conf
#fi

python manage.py migrate --fake-initial
python manage.py collectstatic --no-input

# Remote Django shell not available in production, create an initial superuser account
# cat <<EOF | python manage.py shell
# from django.contrib.auth import get_user_model

# User = get_user_model()

# User.objects.filter(email='jonne.airaksinen@perfektio.fi').exists() or \
#     User.objects.create_superuser('jonne.airaksinen@perfektio.fi', 'password')
# EOF

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