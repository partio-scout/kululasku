now=$(date)

echo start alarming users, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py alarm_unactive_users" >> /mnt/storage/logs/user_logs.txt
echo user alarming over
