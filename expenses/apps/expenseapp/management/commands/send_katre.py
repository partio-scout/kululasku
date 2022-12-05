from django.core.management.base import BaseCommand, CommandError
from expenseapp.models import Expense, ExpenseLine
import os
from datetime import date, datetime, timedelta
from django.conf import settings
from django.core.mail import mail_admins
from django.utils import timezone
import paramiko
import io


class Command (BaseCommand):
    help = 'Sends Katre XML to handling'

    def handle(self, *args, **options):
        end = date.today().replace(day=1) - timedelta(days=1)

        expenses = Expense.objects.filter(
            katre_status=0,
            organisation__send_active=1,
            created_at__gte=datetime(2020, 1, 1, tzinfo=timezone.utc),
            created_at__lte=datetime(
                end.year,
                end.month,
                end.day,
                tzinfo=timezone.utc
            )
        )

        if not expenses:
            self.stdout.write('No katres to send.')
            return
        else:
            self.stdout.write(
                "Found %s expenses to be handled as katre" % str(len(expenses)))

        try:
            katrecount = 0

            IR_USER = os.getenv('IR_USER')
            IR_SERVER = os.getenv('IR_SERVER')
            IR_PORT = 22
            key = paramiko.RSAKey.from_private_key_file(
                'vero-key-test.pem', password=os.getenv('VERO_PRIVATE_KEY_PASSPHRASE'))

            transport = paramiko.Transport((
                IR_SERVER,
                IR_PORT
            ))
            transport.connect(
                username=IR_USER,
                pkey=key
            )
            sftp = paramiko.SFTPClient.from_transport(transport)

            for expense in expenses:

                self.stdout.write('Packaging expense %s...' % expense.pk)

                if expense.needsKatre():
                    xml = expense.katre()
                    data = io.StringIO(xml.decode())
                    name = f'100_{expense.id}'
                    res = sftp.putfo(
                        fl=data,
                        remotepath=f'IN/{name}.tmp',
                        confirm=True
                    )
                    if res.st_size > 0:
                        sftp.rename(
                            f'IN/{name}.tmp',
                            f'IN/{name}.xml'
                        )
                        katrecount = katrecount + 1
                        expense.katre_status = 2
                        expense.save()
                    else:
                        self.stdout.write(
                            f"SFTP failed for expense {expense.id}")
                else:
                    expense.katre_status = 1
                    expense.save()

            self.stdout.write(f'Successfully sent {katrecount} katres')

        except Exception as error:

            self.stdout.write(
                f'Sending expenses to tulorekisteri failed: {str(error)}')

            # Mark expenses unsent in case sending failed
            # expenses.update(katre_status=0)

            mail_admins('Katre sending failed',
                        f'For some reason katre sending failed in kululasku-system. Please check and fix.\n\n{str(error)}')
