echo start sending
docker-compose exec web bash -c "python manage.py send_invoices"
docker-compose exec web bash -c "python manage.py send_katre"
echo cron run is over
