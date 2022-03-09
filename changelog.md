# Changes made in March 9 2022

- new management task: alarm_unactive_users. A crontab command run once a month, 10th day of the month. Sends email for users whom have not been logged in for 2 years.
- new management task: remove_unactive_users. A crontab command run once a month, 10th day of the month. Removes the users whom have been alarmed a month ago.
- removed old, unused db table: registration_registrationprofile.
- removed old, unused db table: parsley_student.
- Added model level valdiations for receipts.

# Changes made in March 4 2022

- Removed expenses memo object from visual fields. DB and model still contains the info for easier backward compatibility
- expense form has new translations
- expenseline formset has new JS-feature: show basis_text depending on the chosen expense type

# Changes made in Feb 23 2022

- sendgrid package update
- removed useless package selenium
- send_email function was the cause of double expenses. Code errored and users went back and tried again. Fix was made and packages updates. Error occurred due to LTS upgrade.

# Changes made in Q1/2022

- postgres:12.9-alpine image in use
- ENV PYTHONWARNINGS="always" flag added to dockerfile
- url updated: reset password
- url updated: password-reset done
- django==3.2.12
- unit tests for
- - login
- - logout
- - expense creation with no file
- - expense creation with a file
- - updating userinfo
