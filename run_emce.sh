now=$(date)

echo start sending invoices, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py send_invoices" >> /mnt/storage/logs/fennoa_logs_2023.txt
echo invoice script over
