from calendar import c
import os
from django.core.management.base import BaseCommand
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.timezone import now


def alarm_user(email):
    from django.core.mail import send_mail
    if email:
        print(f"alarm user: {email}")
        # Send email
        html_text = """
<html>
    <head>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Paytone+One&display=swap" rel="stylesheet">

    <style>
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Paytone One', sans-serif;

    }

    </style>
    </head
    <body>
        <p>Hei,</p> 
        <p>Huomasimme, että edellisestä kirjautumisestasi kululaskujärjestelmään on kulunut yli kaksi vuotta.</p>
        <p>Poistamme palvelusta epäaktiiviset käyttäjät.</p>
        <p>Mikäli et halua, että tilisi poistetaan, kirjaudu kululaskupalveluun 30 vuorokauden sisällä.</p>
        <h2><a href="https://kululasku.partio.fi/">KIRJAUDU KULULASKUPALVELUUN</a></h2>
        <h3>Jos et enää tarvitse käyttäjätiliäsi, sinun ei tarvitse tehdä mitään.</h3>
        <p>Yli kaksi vuotta vanhat tilit poistetaan automaattisesti 30 päivää tämän viestin lähettämisestä.</p>
        <p>Voit milloin tahansa luoda uuden käyttäjätilin osoitteessa <a href="https://kululasku.partio.fi/accounts/register/">https://kululasku.partio.fi/accounts/register/</a></p>
        <p>Terveisin,</p>

        <p>Suomen Partiolaiset – Finlands Scouter ry</p>
        <p>Töölönkatu 55, 00250 Helsinki</p>
        <p><a href="https://partio.fi">www.partio.fi</a></p>
        <p>palvelu@partio.fi</p>
        <br>

        <p> - - - - - - - - - - - - </p>
        
        <br>

        <p>Hej,</p> 
        <p>Vi märkte att din senaste inloggning i kostnadsersättningssystemet var över två år sedan.</p>
        <p>Vi raderar inaktiva användarkonton från systemet.</p>
        <p>Ifall du inte vill att ditt användarkonto raderas, logga in i kostnadsersättningssystemet inom 30 dagar.</p>
        <h2><a href="https://kululasku.partio.fi/">LOGGA IN</a></h2>
        <h3>Ifall du inte längre behöver ditt användarkonto behöver du inte göra något.</h3>
        <p>Konton som varit oanvända i två år eller längre raderas automatiskt inom 30 dagar från och med detta meddelande.</p>
        <p>Du kan när som helst skapa ett nytt användarkonto här: <a href="https://kululasku.partio.fi/accounts/register/">https://kululasku.partio.fi/accounts/register/</a></p>
        <p>Med vänliga hälsningar,</p>

        <p>Suomen Partiolaiset – Finlands Scouter ry</p>
        <p>Töölönkatu 55, 00250 Helsinki</p>
        <p><a href="https://partio.fi">www.partio.fi</a></p>
        <p>palvelu@partio.fi</p>
        <br>
        <p> - - - - - - - - - - - - </p>
        <br>

        <p>Hello,</p> 
        <p>We noticed that your last sign in to the invoice expense system was more than two years ago.</p>
        <p>Inactive accounts will be deleted automatically.</p>
        <p>If you want to keep your account active, sign in to the invoice expense system within 30 days from the date of this message.</p>
        <h2><a href="https://kululasku.partio.fi/">SIGN IN</a></h2>
        <h3>If you no longer need your account, you don’t have to do anything.</h3>
        <p>Accounts that have been inactive for more than [two years] will be deleted automatically 30 days from the date of this message.</p>
        <p>You can create a new account at any time at: <a href="https://kululasku.partio.fi/accounts/register/">https://kululasku.partio.fi/accounts/register/</a></p>
        <p>Best regards,</p>

        <p>Suomen Partiolaiset – Finlands Scouter ry</p>
        <p>Töölönkatu 55, 00250 Helsinki</p>
        <p><a href="https://partio.fi">www.partio.fi</a></p>
        <p>palvelu@partio.fi</p>
    </body>
</html>
"""

# VAIHDA lähettäjä email
        try:
            result = send_mail('Ilmoitus kululasku.partio.fi:sta | Meddelande från kululasku.partio.fi | Notice from kululasku.partio.fi',
                               """
                  Hei, 
Huomasimme, että edellisestä kirjautumisestasi kululaskujärjestelmään on kulunut yli kaksi vuotta.
Poistamme palvelusta epäaktiiviset käyttäjät.
Mikäli et halua, että tilisi poistetaan, kirjaudu kululaskupalveluun 30 vuorokauden sisällä.
https://kululasku.partio.fi/
Jos et enää tarvitse käyttäjätiliäsi, sinun ei tarvitse tehdä mitään.
Yli kaksi vuotta vanhat tilit poistetaan automaattisesti 30 päivää tämän viestin lähettämisestä.
Voit milloin tahansa luoda uuden käyttäjätilin osoitteessa https://kululasku.partio.fi/accounts/register/
Terveisin,

Suomen Partiolaiset – Finlands Scouter ry
Töölönkatu 55, 00250 Helsinki
www.partio.fi
palvelu@partio.fi

- - - - - - - - - -

Hej, 
Vi märkte att din senaste inloggning i kostnadsersättningssystemet var över två år sedan.
Vi raderar inaktiva användarkonton från systemet.
Ifall du inte vill att ditt användarkonto raderas, logga in i kostnadsersättningssystemet inom 30 dagar.
https://kululasku.partio.fi/
Ifall du inte längre behöver ditt användarkonto behöver du inte göra något.
Konton som varit oanvända i två år eller längre raderas automatiskt inom 30 dagar från och med detta meddelande.
Du kan när som helst skapa ett nytt användarkonto här: https://kululasku.partio.fi/accounts/register/
Med vänliga hälsningar,

Suomen Partiolaiset – Finlands Scouter ry
Töölönkatu 55, 00250 Helsinki
www.partio.fi
palvelu@partio.fi

- - - - - - - - - -


Hello, 
We noticed that your last sign in to the invoice expense system was more than two years ago.
Inactive accounts will be deleted automatically.
If you want to keep your account active, sign in to the invoice expense system within 30 days from the date of this message.
https://kululasku.partio.fi/
If you no longer need your account, you don’t have to do anything.
Accounts that have been inactive for more than two years will be deleted automatically 30 days from the date of this message.
You can create a new account at any time at: https://kululasku.partio.fi/accounts/register/
Best regards,

Suomen Partiolaiset – Finlands Scouter ry
Töölönkatu 55, 00250 Helsinki
www.partio.fi
palvelu@partio.fi""",
                               'no-reply@partio.fi', [email], False, html_message=html_text)
            print(f"Result for {email}: {result}")
        except Exception as e:
            print(f"Failed sending {email}. Error: {e}")


class Command (BaseCommand):
    help = 'Sends emails for users with last login time over 2 years ago and emails them.'

    def handle(self, *args, **options):
        today = now()
        print(f'Start alarming unactive users, timestamp: {today}')
        inactiveusers = User.objects.filter(
            last_login__lte=today - timedelta(days=365*2))

        print(f'Users to be alarmed timestamp: {inactiveusers.count()}')

        for user in inactiveusers:
            alarm_user(user.email)
