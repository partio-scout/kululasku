now=$(date)

echo start sending invoices, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py send_invoices" >> /mnt/storage/logs/emce_logs_2022.txt
echo invoice script over

echo start sending katres, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py send_katre" >> /mnt/storage/logs/emce_logs_2022.txt
echo katre script over
