now=$(date)

echo start sending katres, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py send_katre" >> /mnt/storage/logs/vero_logs_2023.txt
echo katre script over
