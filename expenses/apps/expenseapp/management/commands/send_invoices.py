from socket import send_fds
from django.core.management.base import BaseCommand, CommandError
from expenseapp.models import Expense, ExpenseLine
import os
import time
import os.path
import time
import json
import requests
from decimal import Decimal
from requests.auth import HTTPBasicAuth
from PIL import Image
from schwifty import IBAN
from django.core.mail import mail_admins

class Command (BaseCommand):
    help = 'Sends new invoices as XML to handling'
    
    def fetch_supplier(self, url, auth, supplier_id):
        page = 1
        while True:
            suppliers_request = requests.get(
                f'{url}/purchases_api/get/suppliers?page={page}',
                auth=auth
            )

            status = suppliers_request.status_code
            data =  suppliers_request.json()['data']

            if status == 200 and type(data) is list and len(data) > 0:
                filtered = [s for s in data if s['PurchaseSupplier']['business_id'] == supplier_id]
                if len(filtered) > 0:
                    return filtered[0]['PurchaseSupplier']
            else:
                break
            page = page + 1

        return None

    def handle(self, *args, **options):
        BASEURL = os.getenv('FENNOA_APIURL')
        CREDENTIALS_MAP = json.load(open('fennoa_credentials.json'))

        expenses = Expense.objects.filter(
            status=0, organisation__send_active=1)
        if not expenses:
            self.stdout.write('No invoices to send.')
            return
        else:
            self.stdout.write(
                "Found %s expenses to be handled as invoice" % str(len(expenses)))
        try:
            i = 0
            for expense in expenses:
                CREDS = CREDENTIALS_MAP[expense.organisation.business_id]
                USER = CREDS["user"]
                TOKEN = CREDS["token"]
                basic = HTTPBasicAuth(USER, TOKEN)

                supplier = self.fetch_supplier(
                    BASEURL,
                    basic,
                    expense.user.id
                )

                j = 1

                purchase_data = {
                    'purchase_invoice_type_id': 1,
                    'invoice_number': expense.id,
                    'invoice_date': expense.created_at.strftime('%Y%m%d'),
                    'due_date': expense.created_at.strftime('%Y%m%d'),
                    'bank_message': expense.description,
                    'total_net': str(expense.amount()),
                    'total_gross': str(expense.amount()),
                }
                if supplier != None:
                    supplier_data = {
                        'purchase_supplier_id': supplier.id,
                        'supplier_name': supplier.name,
                        'supplier_business_id': supplier.business_id,
                        'bank_account': supplier.bank_account,
                        'bank_bic': supplier.bank_bic,
                        'supplier_country': supplier.country_id,
                    }
                else:
                    supplier_data = {
                        'supplier_name': expense.name,
                        'supplier_business_id': expense.user.id,
                        'bank_account': expense.iban,
                        'bank_bic': str(IBAN(expense.iban).bic),
                        'supplier_country': 'FI'
                    }

                purchase_payload = {
                    **purchase_data,
                    **supplier_data
                }

                purchase_request = requests.post(
                    f'{BASEURL}/purchases_api/add',
                    json=purchase_payload,
                    auth=basic
                )

                if purchase_request.status_code == 200:
                    expense.status = 1
                    expense.save
                    purchase_res_data = purchase_request.json()
                    if 'saved_ids' in purchase_res_data:
                        invoice_id = purchase_res_data['saved_ids']['purchase_invoice_id']
                    else:
                        invoice_id = purchase_res_data['id']

                    self.stdout.write('Created purchase invoice for expense %s.' % expense.pk)

                    tags_payload = {
                        'json': json.dumps(
                            expense.accounts()
                        )
                    }

                    tags_request = requests.post(
                        f'{BASEURL}/purchases_api/do/set_tags/{invoice_id}',
                        json=tags_payload,
                        auth=basic
                    )

                    if tags_request.status_code == 200:
                        self.stdout.write('Created tags for expense %s...' % expense.pk)
                    else:
                        self.stdout.write('Failed creating tags for expense %s...' % expense.pk)
                    
                    lines = ExpenseLine.objects.filter(expense=expense)
                    
                    for line in lines:
                        if line.receipt:
                            receiptpath = line.receipt.path
                            if not '.pdf' in line.receipt.name.lower():
                                try:
                                    im = Image.open(line.receipt.path)
                                except IOError:
                                    self.stdout.write(
                                        'Not able to convert receipt ' + \
                                        line.receipt.path
                                    )
                                    mail_admins(
                                        "File handling failed",
                                        "Not able to convert receipt" + \
                                        line.receipt.path + \
                                        "in kululasku-system."
                                    )
                                    continue
                                if not im:
                                    continue
                                receiptpath = '/tmp/zips/receipttemp_' + \
                                    str(j) + '.pdf'
                                # ValueError might mean that PIL doesn't
                                # know how to strip alpha off the image:
                                # http://www.daniweb.com/software-development/python/threads/253957/converting-an-image-file-png-to-a-bitmap-file
                                try:
                                    im.save(
                                        receiptpath,
                                        "PDF",
                                        resolution=200.0
                                    )
                                except ValueError:
                                    r, g, b, a = im.split()
                                    img = Image.merge("RGB", (r, g, b))
                                    img.save(
                                        receiptpath,
                                        "PDF",
                                        resolution=200.0
                                    )

                            filename = f'liite_{str(expense.id)}_{str(j).zfill(3)}{os.path.splitext(str(receiptpath))[1]}'
                            files = {
                                'file': (
                                    filename,
                                    open(receiptpath, 'rb'),
                                    'application/pdf'
                                )
                            }
                            url = f'{BASEURL}/purchases_api/do/upload_attachment/{invoice_id}'
                            r = requests.post(
                                url,
                                files=files,
                                auth=basic
                            )
                        j = j + 1

                    i = i + 1
                else:
                    self.stdout.write('Failed to create purchase invoice for expense %s...' % expense.pk)

            expenses.update(status=1)
            self.stdout.write('Successfully sent %s invoices' % i)

        except Exception as error:
            self.stdout.write("Package sending failed: %s" % str(error))
            # Mark expenses unsent in case sending failed
            expenses.update(status=0)
            mail_admins("Invoice sending failed",
                        "For some reason invoice sending failed in kululasku-system. Please check and fix.\n\n%s" % str(error))
