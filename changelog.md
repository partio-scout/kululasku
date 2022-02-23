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
