from django.core.management.base import BaseCommand
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.timezone import now


def cc_expense(email):
    from django.core.mail import send_mail
    if email:
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
    </body>
</html>
"""

        # body = render_to_string('base.html')
# VAIHDA lähettäjä email
        send_mail('Käyttäjätilisi automaattinen poisto Suomen Partiolaisten kululaskujärjestelmästä',
                  'Tää on kyl melkone :D',
                  'no-reply@partio.fi', [email], False, html_message=html_text)


class Command (BaseCommand):
    help = 'Sends emails for users with last login time over 2 years ago and emails them.'

    def handle(self, *args, **options):
        today = now()
        inactiveusers = User.objects.filter(
            last_login__lte=today - timedelta(days=365*2))

        print(22, inactiveusers.count(), inactiveusers.first().expense_set)
        cc_expense('sami.lindqvist@perfektio.fi')
