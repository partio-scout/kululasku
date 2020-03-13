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

### Create translation files and apply them

```
docker-compose exec web cd expenses/apps/expenseapp/ && django-admin makemessages -l=fi && django-admin makemessages -l=sv && django-admin compilemessages --use-fuzzy
```

### You can edit the translation files and whenever ready, run

```
docker-compose exec web cd expenses/apps/expenseapp/ && django-admin compilemessages --use-fuzzy
```

### SQL query to force start times for expensetypes that have requires_endtime = True;
```
docker-compose exec  db psql -U postgres
update expenseapp_expensetype set requires_start_time = True where requires_endtime = True;
```