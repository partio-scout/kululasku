now=$(date)

echo start sending invoices, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py send_invoices" >> /mnt/storage/logs/emce_logs.txt
echo invoice script over

echo start sending katres, $now
docker-compose -f docker-compoes-prod.yml exec -T web bash -c "python manage.py send_katre" >> /mnt/storage/logs/emce_logs.txt
echo katre script over
