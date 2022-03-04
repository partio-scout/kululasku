# Partio Kululaskujärjestelmä

## Kuvaus

Kululaskujärjestelmä on Suomen Partiolaisten käyttämä verkkopalvelu kululaskujen käsittelyyn.

Tech stack:

- Python3
- Django 2.2.x LTS
- nginx
- gunicorn
- Docker
- Sendgrid

## Huomioitavaa

- Palvelu on integroitu <a href="https://www.emce.fi/">EmCen</a> palveluun, joka on ulkoinen suljettu järjestelmä, minkä vuoksi palvelun kokonaan käyttöönotettavaksi vaatii yhteydenottoa ja neuvottelua <a href="https://www.emce.fi/">EmCen</a> kanssa.
- Jos integroit EmCeen aseta crontab esimerkin tapaan, crontab -e komennolla

## Käyttöönottoa varten

- Tarkista .env file kuntoon, esimerkkinä toimii env_example
- Tarkista docker-compose.yml filen volumet kuntoon
- vaihda settings/**init**.py tiedoston allowed hosts asianmukaiseksi

#Tarkista seuraavat tiedot erityisen tarkasti

- settings/**init**.py tiedosto
- sähköpostien templatejen muuttujat
- Käännösten tekstisisällöt
- send_invoices.py
- send_katre.py
- katre.py muuttujat
- Jokainen #VAIHDA kohta repossa

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

### Put the Maintenance mode on

```
mv maintenance_off.html maintenance_on.html
```

### Put the Maintenance mode off

```
mv maintenance_on.html maintenance_off.html
```

### Django migrations

```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Create translation files and apply them

```
docker-compose exec web bash -c "cd expenses/apps/expenseapp/ && django-admin makemessages -l=fi && django-admin makemessages -l=sv && django-admin compilemessages --use-fuzzy"
```

### You can edit the translation files and whenever ready, run

```
docker-compose exec web bash -c "cd expenses/apps/expenseapp/ && django-admin compilemessages --use-fuzzy"
```

### SQL query to force start times for expensetypes that have requires_endtime = True;

```
docker-compose exec  db psql -U postgres
update expenseapp_expensetype set requires_start_time = True where requires_endtime = True;
```

### Tietokannan restoraus

```
docker-compose down && docker-compose up -d db && docker-compose exec db sh -c "dropdb -U postgres postgres" && docker-compose exec db createdb -U postgres -T template0 postgres && docker-compose exec -T db psql -U postgres postgres < tmp/db_dumps/DUMPPI_FFILU.sql
```

### Tietokannan kopiointi

```
docker-compose exec db  pg_dump -U $DB_USER $DB_NAME > ./dump_$DATESTAMP.sql
```

### Testien ajaminen

`docker-compose up -d && docker-compose exec web bash -c "python manage.py test expenseapp" && docker-compose down`
