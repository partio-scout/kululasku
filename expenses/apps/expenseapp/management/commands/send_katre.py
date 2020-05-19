from django.core.management.base import BaseCommand, CommandError
from expenseapp.models import Expense, ExpenseLine
import os, time
import os.path
import random, string
from datetime import date, datetime
from django.conf import settings
from django.core.mail import mail_admins
from django.utils import timezone

class Command (BaseCommand):
  help = 'Sends Katre XML to handling'

  def handle(self, *args, **options):
    expenses = Expense.objects.filter(
      katre_status=0,
      organisation__send_active=1, 
      created_at__gte=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )

    if not expenses:
      self.stdout.write('No katres to send.')
      return
    else:
      self.stdout.write("Found %s expenses to be handled as katre" % str(len(expenses)))

    try:

      import zipfile, io

      date_str = datetime.now().strftime("%Y-%m-%d-%H-%M")
      o = os.path.join('/tmp/zips', 'katre_' + date_str + '.zip')
      h = os.path.join('/tmp/zips', 'katre_hapa_' + date_str + '.zip')
      
      self.stdout.write('Creating katre package %s' % o)

      katre_zip = zipfile.ZipFile(o, mode='w')
      hapa_zip = zipfile.ZipFile(h, mode='w')

      katrecount = 0
      hapacount = 0

      for expense in expenses:

        self.stdout.write('Packaging expense %s...' % expense.pk)

        if expense.needsKatre():
          xml = expense.katre()
          #Hämeenpartiopiirin y-tunnus, Muokattava jos halutaan muille käyttöön
          if expense.organisation.katre_cert_business_id == '0288930-9':
            hapa_zip.writestr('katre_hapa_' + str(expense.id) + '.xml', xml)
            hapacount = hapacount + 1
          else:
            katre_zip.writestr('katre_' + str(expense.id) + '.xml', xml)
            katrecount = katrecount + 1

          expense.katre_status = 2

        else:
          expense.katre_status = 1

      katre_zip.close()
      hapa_zip.close()

      self.stdout.write('Packaging done.')
      
      if katrecount > 0 or hapacount > 0:
        import paramiko
        EMCE_USERNAME = os.getenv('EMCE_USERNAME')
        EMCE_PASSWORD = os.getenv('EMCE_PASSWORD')
        EMCE_SERVER = os.getenv('EMCE_SERVER')
        EMCE_SERVER_PORT = os.getenv('EMCE_SERVER_PORT')

        transport = paramiko.Transport((EMCE_SERVER, EMCE_SERVER_PORT))
        transport.connect(username=EMCE_USERNAME, password=EMCE_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir('siirto')
        sftp.chdir('katre')
        
        if katrecount > 0:
          output_file_name = 'katre_' + date_str + '.zip'
          self.stdout.write('Sending %s...' % output_file_name)
          sftp.put(o, output_file_name)

        if hapacount > 0:
          hapa_file_name = 'katre_hapa_' + date_str + '.zip'
          self.stdout.write('Sending %s...' % hapa_file_name)
          sftp.chdir('hapa')
          sftp.put(h, hapa_file_name)

        self.stdout.write('Packages sent, closing connection...')

        transport.close()
      #Save the changes to DB. Value calculated earlier, so needs save not update.
      for expense in expenses:
        expense.save()
            
      self.stdout.write('Successfully sent %s katres' % str(katrecount + hapacount))

    except Exception as error:

      self.stdout.write("Package sending failed: %s" % str(error))

      # Mark expenses unsent in case sending failed
      expenses.update(katre_status=0)

      mail_admins("Katre sending failed", "For some reason katre sending failed in kululasku-system. Please check and fix.\n\n%s" % str(error))

    #os.remove(o)

