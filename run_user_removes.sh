now=$(date)

echo start removing users, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py remove_unactive_users" >> /mnt/storage/logs/removed_user_logs.txt
echo user removal over
