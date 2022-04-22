import os
from django.core.management.base import BaseCommand
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.timezone import now


class Command (BaseCommand):
    help = 'Reactivate users with last login time 2 years and 1 month ago.'

    def handle(self, *args, **options):
        today = now()
        inactiveusers = User.objects.filter(
            last_login__lte=(today - timedelta(days=(365*2 + 30))))

        print(f'Start deactivating unactive users, timestamp: {today}')
        print(f'Prepare to deactivate {inactiveusers.count()} users')

        for user in inactiveusers:
            user.is_active = False
            user.save()
