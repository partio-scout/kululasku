from django.core.management.base import BaseCommand, CommandError
from expenseapp.models import Expense, ExpenseLine
import os, time
import os.path
import random, string
import time
from PIL import Image
from datetime import date, datetime
from django.conf import settings
from django.core.mail import mail_admins

class Command (BaseCommand):
  help = 'Sends new invoices as XML to handling'

  def handle(self, *args, **options):
    expenses = Expense.objects.filter(status=0, organisation__send_active=1)
    if not expenses:
      self.stdout.write('No invoices to send.')
      return

    try:

      import zipfile, io
      
      date_str = datetime.now().strftime("%Y-%m-%d-%H-%M")
      o = os.path.join("/tmp/zips", date_str + '.zip')
      
      self.stdout.write('Creating package %s' % o)

      zf = zipfile.ZipFile(o, mode='w')

      i = 0
      for expense in expenses:

        self.stdout.write('Packaging expense %s...' % expense.pk)

        j = 1
        xml = expense.finvoice()
        zf.writestr('lasku_' + str(expense.id) + '.xml', xml)

        lines = ExpenseLine.objects.filter(expense=expense)
        for line in lines:
          if line.receipt:
            receiptpath = line.receipt.path
            if not '.pdf' in line.receipt.name.lower():
              try:
                im = Image.open(line.receipt.path)
              except IOError:
                self.stdout.write('Not able to convert receipt ' + line.receipt.path)
                mail_admins("File handling failed", "Not able to convert receipt" + line.receipt.path + "in kululasku-system.")
                continue
              if not im:
                continue
              receiptpath = '/tmp/zips/receipttemp_' + str(j) + '.pdf'
              # ValueError might mean that PIL doesn't know how to strip alpha off the image:
              # http://www.daniweb.com/software-development/python/threads/253957/converting-an-image-file-png-to-a-bitmap-file
              try:
                im.save(receiptpath, "PDF", resolution=200.0)
              except ValueError:
                r, g, b, a = im.split()
                img = Image.merge("RGB", (r, g, b))
                img.save(receiptpath, "PDF", resolution=200.0)

            zf.write(receiptpath, 'liite_' + str(expense.id) + '_' + str(j).zfill(3) + os.path.splitext(str(receiptpath))[1])
          j = j + 1

        expense.status = 1
        expense.save()

        i = i + 1

      zf.close()

      self.stdout.write('Packaging done.')
      
      import paramiko

      USERNAME = os.getenv('USERNAME')
      PASSWORD = os.getenv('PASSWORD')
      SERVER_ADDRESS = os.getenv('SERVER_ADDRESS')
      SERVER_ATTR = os.getenv('SERVER_ATTR')
      
      transport = paramiko.Transport((SERVER_ADDRESS, SERVER_ATTR))
      transport.connect(username=USERNAME, password=PASSWORD)
      sftp = paramiko.SFTPClient.from_transport(transport)

      output_file_name = str(time.time()) + '.zip'
      self.stdout.write('Sending %s...' % output_file_name)

      sftp.chdir('siirto')
      sftp.put(o, output_file_name)

      self.stdout.write('Package sent, closing connection...')

      transport.close()

      self.stdout.write('Done.')

      expenses.update(status=1)

    except Exception as error:

      print("Package sending failed: %s" % str(error))

      # Mark expenses unsent in case sending failed
      expenses.update(status=0)

      mail_admins("Invoice sending failed", "For some reason invoice sending failed in kululasku-system. Please check and fix.\n\n%s" % str(error))
    self.stdout.write('Successfully sent %s invoices' % i)