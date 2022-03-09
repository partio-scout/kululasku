import os
from django.core.management.base import BaseCommand
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.timezone import now
from expenses import settings
from expenseapp.models import Expense, ExpenseLine, Person


def remove_expense_lines_receipt(expense_line):
    if not expense_line.receipt:
        return
    try:
        os.remove(os.path.join(settings.MEDIA_ROOT, expense_line.receipt.name))
        print(os.path.join(settings.MEDIA_ROOT, expense_line.receipt.name))
    except Exception as e:
        print('ERROR', e)


def remove_expenses_line(expense):
    expense_lines = ExpenseLine.objects.filter(expense=expense)
    for line in expense_lines:
        remove_expense_lines_receipt(line)
    expense_lines.delete()


def remove_users_data(user):
    expenses = Expense.objects.filter(user=user)
    if expenses.exists():
        for expense in expenses:
            remove_expenses_line(expense)
        expenses.delete()

    person = Person.objects.filter(user=user)
    if person.exists():
        person.delete()
    user.delete()


class Command (BaseCommand):
    help = 'Removes users with last login time 2 years and 1 month ago.'

    def handle(self, *args, **options):
        today = now()
        inactiveusers = User.objects.filter(
            last_login__lte=today - timedelta(days=(365*2 + 30)))

        print(f'Start removing unactive users, timestamp: {today}')
        print(f'Prepare to remove {inactiveusers.count()} users')

        for user in inactiveusers:
            remove_users_data(user)
