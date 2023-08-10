from django.core.management.base import BaseCommand, CommandError
from expenseapp.models import Expense, ExpenseLine
import os
import time
import os.path
import time
import json
import requests
from lxml import etree
import pdfkit
from requests.auth import HTTPBasicAuth
from PIL import Image
from schwifty import IBAN
from django.core.mail import mail_admins


class Command (BaseCommand):
    help = 'Sends new invoices to Fennoa API'

    def fetch_supplier(self, url, auth, supplier_id, supplier_name):
        page = 1
        while True:
            self.stdout.write(f'fetching suppliers page {page}')
            suppliers_request = requests.get(
                f'{url}/purchases_api/get/suppliers?page={page}',
                auth=auth
            )

            status = suppliers_request.status_code
            data = suppliers_request.json()['data']

            if status == 200 and type(data) is list and len(data) > 0:
                # self.stdout.write(f'{data}')
                filtered = [s for s in data if s['PurchaseSupplier']
                            ['name'] == supplier_name]
                if len(filtered) > 0:
                    self.stdout.write(f'Found existing supplier {supplier_id} {supplier_name}')
                    return filtered[0]['PurchaseSupplier']
            else:
                self.stdout.write(f'Found no supplier {supplier_id} {supplier_name}')
                break
            page = page + 1

        return None

    def upload_file(self, filename, path, url, auth):
        files = {
            'file': (
                filename,
                open(path, 'rb'),
                'application/pdf'
            )
        }
        file_request = requests.post(
            url,
            files=files,
            auth=auth
        )

        if file_request.status_code == 200:
            self.stdout.write(f'Successfully uploaded file {filename}')
        else:
            self.stdout.write(f'Failed uploading file {filename}')

        return file_request

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
                f'Found {str(len(expenses))} expenses to be handled as invoice')
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
                    str(expense.user.id),
                    expense.name
                )

                j = 1
                self.stdout.write(f'Sending expense {expense.pk} data')
                invoice_type = 1 if expense.amount() > 0 else 2

                purchase_data = {
                    'purchase_invoice_type_id': invoice_type,
                    'invoice_number': expense.id,
                    'invoice_date': expense.created_at.strftime('%Y-%m-%d'),
                    'due_date': expense.created_at.strftime('%Y-%m-%d'),
                    'bank_message': expense.description,
                    'total_net': str(expense.amount()),
                    'total_gross': str(expense.amount()),
                }
                if supplier != None:
                    supplier_data = {
                        'purchase_supplier_id': supplier['id'],
                        'supplier_name': supplier['name'],
                        # 'supplier_business_id': supplier['business_id'],
                        'bank_account': supplier['bank_account'],
                        'bank_bic': supplier['bank_bic'],
                        'supplier_country': supplier['country_id'],
                    }
                else:
                    supplier_data = {
                        'supplier_name': expense.name,
                        # 'supplier_business_id': expense.user.id,
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
                self.stdout.write(
                    f'purchase_request status: {purchase_request.status_code}')
                self.stdout.write(f'{purchase_request.json()}')

                if purchase_request.status_code == 200:
                    expense.status = 1
                    expense.save()
                    purchase_res_data = purchase_request.json()
                    if 'saved_ids' in purchase_res_data:
                        invoice_id = purchase_res_data['saved_ids']['purchase_invoice_id']
                    else:
                        invoice_id = purchase_res_data['id']

                    self.stdout.write(
                        f'Created purchase invoice for expense {expense.pk}.')
                    accounts = json.dumps(
                        expense.accounts()
                    )
                    tags_payload = {
                        'json': accounts
                    }
                    self.stdout.write(f'{tags_payload}')
                    tags_request = requests.post(
                        f'{BASEURL}/purchases_api/do/set_tags/{invoice_id}',
                        json=tags_payload,
                        auth=basic
                    )

                    if tags_request.status_code == 200:
                        self.stdout.write(
                            f'Created tags for expense {expense.pk}.')
                    else:
                        self.stdout.write(
                            f'Failed creating tags for expense {expense.pk}.')
                        self.stdout.write(f'{tags_request.json()}')

                    parser = etree.XMLParser(
                        ns_clean=True, recover=True, encoding='utf-8')
                    h = etree.fromstring(expense.finvoice(), parser=parser)
                    xslt = etree.parse('static/Finvoice.xsl')
                    transform = etree.XSLT(xslt)
                    newdom = transform(h)
                    a = etree.tostring(newdom, pretty_print=True)
                    options = {'enable-local-file-access': ''}
                    invoice_pdf_name = f'lasku_{str(expense.id)}.pdf'
                    invoice_pdf_path = f'/tmp/pdfs/{invoice_pdf_name}'
                    html_string = a.decode('utf-8').replace('\n', '')
                    pdfkit.from_string(
                        html_string,
                        invoice_pdf_path,
                        options=options,
                        verbose=True,
                        css='static/Finvoice.css'
                    )
                    self.upload_file(
                        invoice_pdf_name,
                        invoice_pdf_path,
                        f'{BASEURL}/purchases_api/do/upload_attachment/{invoice_id}',
                        basic
                    )

                    lines = ExpenseLine.objects.filter(expense=expense)

                    for line in lines:
                        if line.receipt:
                            receiptpath = line.receipt.path
                            if not '.pdf' in line.receipt.name.lower():
                                try:
                                    im = Image.open(line.receipt.path)
                                except IOError:
                                    self.stdout.write(
                                        'Not able to convert receipt ' +
                                        line.receipt.path
                                    )
                                    mail_admins(
                                        "File handling failed",
                                        "Not able to convert receipt" +
                                        line.receipt.path +
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
                            self.stdout.write(filename)

                            self.upload_file(
                                filename,
                                receiptpath,
                                f'{BASEURL}/purchases_api/do/upload_attachment/{invoice_id}',
                                basic
                            )

                        j = j + 1

                    i = i + 1
                else:
                    self.stdout.write(
                        f'Failed to create purchase invoice for expense {expense.pk}')

            self.stdout.write(f'Successfully sent {i} invoices')

        except Exception as error:
            self.stdout.write(f'Package sending failed: {str(error)}')
            # Mark expenses unsent in case sending failed
            expenses.update(status=0)
            mail_admins('Invoice sending failed',
                        f'For some reason invoice sending failed in kululasku-system. Please check and fix.\n\n{str(error)}')
