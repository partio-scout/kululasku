now=$(date)

echo start renaming xml files, $now
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python manage.py rename_xml_files" >> /mnt/storage/logs/vero_logs_2023.txt
echo rename xml script over
