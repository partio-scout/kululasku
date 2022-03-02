# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy
import locale

# Lähde: http://www.ohjelmointiputka.net/koodivinkit/26782-python-viitenumerolaskuri


def viitenumeron_tarkiste(viitenumero_raaka):
    """palauta annetun tarkisteettoman viitenumeron perään kuuluva tarkistenumero"""
    kertoimet = (7, 3, 1)
    viitenumero_raaka = viitenumero_raaka.replace(' ', '')
    nrot_kaanteinen = list(map(int, viitenumero_raaka[::-1]))
    tulosumma = sum(kertoimet[i % 3] * x for i,
                    x in enumerate(nrot_kaanteinen))
    return (10 - (tulosumma % 10)) % 10


def decimal_in_r82(number):
    return format(number, '.2f').replace('.', ',')


def decimal_without_separator(number):
    return int(round(float(number)*100))


def cc_expense(instance):
    from django.core.mail import send_mail
    from expenseapp.models import ExpenseLine
    if instance.cc_email:
        # Send email
        lines = ExpenseLine.objects.filter(expense=instance)
        rows = gettext_lazy("Date\t\tType\t\tAmount\n")
        rowtemplate = " %s\t%s\t%s×%s=%s\n%s\n\n"
        for line in lines:
            rows = rows + rowtemplate % (line.begin_at.strftime('%d.%m.%Y'), line.expensetype,
                                         line.basis, line.multiplier, locale.currency(line.sum(), False), line.description)

        body = ("""Hi,

You were CC'd in a new expense application for %s.

Name:        %s
Description: %s

Expense lines:
 %s
Total: %s

Best regards,
--
Finnish scout's expense system
""")
# VAIHDA lähettäjä email
        send_mail(str(gettext_lazy('New expense CC\'d to you')),
                  body % (instance.organisation.name, instance.name, instance.description,
                          instance.memo, str(rows), str(locale.currency(instance.amount()))),
                  'no-reply@partio.fi', [instance.cc_email], False)
