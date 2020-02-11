### To apply changes

```
docker-compose build
```

### to run the dev server

```
docker-compose up
```

### Create a superuser

```
docker-compose exec web python manage.py createsuperuser
```

### Create default user permission groups

```
docker-compose exec web python manage.py create-permission-groups
```

### Django migrations

```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Create translation files

```
docker-compose exec web django-admin makemessages -a
```

You can edit the translation files and whenever ready, run

```
docker-compose exec web django-admin compilemessages
