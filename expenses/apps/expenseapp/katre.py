# -*- coding: utf-8 -*-
import os
from locale import currency
from django.utils import timezone
from datetime import datetime
from lxml.etree import Element, SubElement, Comment, tostring, ElementTree
import lxml.etree as etree
from signxml import XMLSigner, SignatureConstructionMethod, SignatureMethod, DigestAlgorithm, CanonicalizationMethod
import uuid
from OpenSSL import crypto

CONTACT_NAME = os.getenv('CONTACT_NAME')
CONTACT_NUM = os.getenv('CONTACT_NUM')


NAMESPACES = {
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'wrtir': 'http://www.tulorekisteri.fi/2017/1/WageReportsToIR',
}


def createKatreReport(expense, expenselines):
    attr_qname = etree.QName(
        "http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")

    root = Element(
        '{%s}WageReportsRequestToIR' % NAMESPACES['wrtir'],
        {attr_qname: "http://www.tulorekisteri.fi/2017/1/WageReportsToIR WageReportsToIR.xsd"},
        nsmap=NAMESPACES)

    top = SubElement(root, 'DeliveryData')

    ts = SubElement(top, 'Timestamp')
    now = datetime.utcnow()
    ts.text = now.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

    s = SubElement(top, 'Source')
    s.text = 'Partio Kululasku'

    ddt = SubElement(top, 'DeliveryDataType')
    ddt.text = '100'

    did = SubElement(top, 'DeliveryId')
    did.text = str(uuid.uuid4())

    fc = SubElement(top, 'FaultyControl')
    fc.text = '1'
    pe = SubElement(top, 'ProductionEnvironment')
    pe.text = "true"

    ddo = SubElement(top, 'DeliveryDataOwner')
    ddo_type = SubElement(ddo, 'Type')
    ddo_type.text = '1'
    ddo_code = SubElement(ddo, 'Code')
    ddo_code.text = expense.organisation.business_id

    ddc = SubElement(top, 'DeliveryDataCreator')
    ddc_type = SubElement(ddc, 'Type')
    ddc_type.text = '1'
    ddc_code = SubElement(ddc, 'Code')
    ddc_code.text = expense.organisation.katre_cert_business_id

    dds = SubElement(top, 'DeliveryDataSender')
    dds_type = SubElement(dds, 'Type')
    dds_type.text = '1'
    dds_code = SubElement(dds, 'Code')
    dds_code.text = expense.organisation.katre_cert_business_id

    pp = SubElement(top, 'PaymentPeriod')
    pd = SubElement(pp, 'PaymentDate')
    pd.text = now.strftime('%Y-%m-%d')
    sd = SubElement(pp, 'StartDate')
    
    earliest_start = [x.begin_at for x in expenselines.order_by('begin_at')][0]
    latest_end = [x.ended_at for x in expenselines.order_by('ended_at')][-1]

    if latest_end == None:
        latest_end = earliest_start

    sd.text = earliest_start.strftime('%Y-%m-%d')
    ed = SubElement(pp, 'EndDate')
    ed.text = latest_end.strftime('%Y-%m-%d')

    # VAIHDA
    cp = SubElement(top, 'ContactPersons')
    cpp = SubElement(cp, 'ContactPerson')
    cpn = SubElement(cpp, 'Name')
    cpn.text = CONTACT_NAME
    cpt = SubElement(cpp, 'Telephone')
    cpt.text = CONTACT_NUM
    cprc = SubElement(cpp, 'ResponsibilityCode')
    cprc.text = '1'

    p = SubElement(top, 'Payer')
    pids = SubElement(p, 'PayerIds')
    pidsid = SubElement(pids, 'Id')
    pidsid_type = SubElement(pidsid, 'Type')
    pidsid_type.text = '1'
    pidsid_code = SubElement(pidsid, 'Code')
    pidsid_code.text = expense.organisation.business_id

    r = SubElement(top, 'Reports')
    rp = SubElement(r, 'Report')

    rd = SubElement(rp, 'ReportData')
    rda = SubElement(rd, 'ActionCode')
    rda.text = '1'
    rdid = SubElement(rd, 'ReportId')
    refno = str(expense.created_at.strftime('%Y')) + str(expense.id).zfill(5)
    from expenseapp.helpers import viitenumeron_tarkiste
    rdid.text = expense.organisation.emce_id + '-' + \
        refno + str(viitenumeron_tarkiste(refno))

    rie = SubElement(rp, 'IncomeEarner')
    rieids = SubElement(rie, 'IncomeEarnerIds')
    rieidsid = SubElement(rieids, 'Id')
    rieidsid_type = SubElement(rieidsid, 'Type')
    rieidsid_type.text = '2'
    rieidsid_code = SubElement(rieidsid, 'Code')
    rieidsid_code.text = expense.personno.upper()
    rieieb = SubElement(rie, 'IncomeEarnerBasic')
    if expense.name == (expense.user.first_name + ' ' + expense.user.last_name):
        lastName = expense.user.last_name
        firstName = expense.user.first_name
    else:
        splitName = expense.name.split(' ', 1)
        lastName = splitName[1]
        firstName = splitName[0]
    rieieb_ln = SubElement(rieieb, 'LastName')
    rieieb_ln.text = lastName
    rieieb_fn = SubElement(rieieb, 'FirstName')
    rieieb_fn.text = firstName

    t = SubElement(rp, 'Transactions')

    diemtypes = ['FPD', 'PPD', 'FOPD', 'MA']
    diemtypecodes = {'FPD': '3', 'PPD': '2', 'FOPD': '4', 'MA': '1'}
    totals = {'km': 0, 'kmsum': 0, 'FPD': 0, 'PPD': 0, 'FOPD': 0, 'MA': 0}
    km_transaction_code = '357'

    for line in expenselines:
        if not line.expensetype_type in ['FPD', 'PPD', 'FOPD', 'MA', 'T']:
            continue

        if line.expensetype_type == 'T':
            totals['km'] += line.basis
            totals['kmsum'] += line.sum()

            # Account 6200 == Employee and 4400 == Employee
            if line.expensetype.account == '6200' or line.expensetype.account == '4400':
                km_transaction_code = '311'

        if line.expensetype_type in diemtypes:
            totals[line.expensetype_type] += line.sum()

    if totals['kmsum'] > 0:
        tr = SubElement(t, 'Transaction')

        trb = SubElement(tr, 'TransactionBasic')
        trb_code = SubElement(trb, 'TransactionCode')
        trb_code.text = km_transaction_code
        trb_amount = SubElement(trb, 'Amount')
        trb_amount.text = str(round(totals['kmsum'], 2))

        if km_transaction_code == '311':
            trkm = SubElement(tr, 'KmAllowance')
            trkms = SubElement(trkm, 'Kilometers')
            trkms.text = str(int(round(totals['km'])))

    for diemtype in diemtypes:
        if totals[diemtype] > 0:
            tr = SubElement(t, 'Transaction')

            trb = SubElement(tr, 'TransactionBasic')
            trb_code = SubElement(trb, 'TransactionCode')
            trb_code.text = '331'
            trb_amount = SubElement(trb, 'Amount')
            trb_amount.text = str(round(totals[diemtype], 2))

            da = SubElement(tr, 'DailyAllowance')
            dat = SubElement(da, 'AllowanceCode')
            dat.text = diemtypecodes[diemtype]

    der = open("vero_sftp.cert", "rb").read()
    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, der)
    pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    key = open("vero-key-test.pem").read()
    signed_root = XMLSigner(
        method=SignatureConstructionMethod.enveloped,
        signature_algorithm=SignatureMethod.RSA_SHA256,
        digest_algorithm=DigestAlgorithm.SHA256,
        c14n_algorithm=CanonicalizationMethod.CANONICAL_XML_1_0
    ).sign(
        root,
        key=key,
        passphrase=bytes(
            os.getenv('VERO_PRIVATE_KEY_PASSPHRASE'),
            'utf-8'
        ),
        cert=pem
    )
    # signature = SubElement(root, 'Signature')
    # signature.text = signed_root

    return tostring(signed_root, encoding='UTF-8', xml_declaration=True)
