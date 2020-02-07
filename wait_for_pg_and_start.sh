#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    #prospector --uses django
    
    echo "Waiting for postgres..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.1
    done

    echo "PostgreSQL started"
    
fi

exec "$@"
