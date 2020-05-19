now=$(date)

echo start sending invoices, $now
docker-compose exec -T web bash -c "python manage.py send_invoices" >> /mnt/storage/logs/emce_logs.txt
echo invoice script over

echo start sending katres, $now
docker-compose exec -T web bash -c "python manage.py send_katre"
echo katre script over