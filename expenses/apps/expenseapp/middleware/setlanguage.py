# -*- coding: utf-8 -*-
from django.utils import translation
from expenseapp.models import Person
from expenses import settings


class ExpenseAppSetLanguageMiddleware(object):
    def process_request(self, request):
        if not request.user.is_authenticated():
            translation.activate(settings.LANGUAGE_CODE)
            return

        try:
            user = Person.objects.get(user=request.user)
            if request.session.get('django_language', None) is not user.language and user.language is not None:
                translation.activate(user.language)
                request.session['django_language'] = user.language
        except Person.DoesNotExist:
            pass
