# -*- coding: utf-8 -*-
from locale import currency
from django.utils import timezone
from lxml.etree import Element, SubElement, tostring
import lxml.etree as etree


def createFinvoice(expense, expenselines):
    top = Element('Finvoice')
    top.set('Version', '1.2')

    top.addprevious(etree.PI('xml-stylesheet',
                    'type="text/xsl" href="Finvoice.xsl"'))

    sp = SubElement(top, 'SellerPartyDetails')
    spi = SubElement(sp, 'SellerPartyIdentifier')
    # Instead of HeTu we use user ID as a identifier
    spi.text = str(expense.user.id)

    spn = SubElement(sp, 'SellerOrganisationName')
    spn.text = expense.name

    spad = SubElement(sp, 'SellerPostalAddressDetails')
    ssn = SubElement(spad, 'SellerStreetName')
    ssn.text = expense.address

    scd = SubElement(top, 'SellerCommunicationDetails')
    sei = SubElement(scd, 'SellerEmailaddressIdentifier')
    sei.text = expense.email
    spni = SubElement(scd, 'SellerPhoneNumberIdentifier')
    spni.text = expense.phone

    si = SubElement(top, 'SellerInformationDetails')
    sa = SubElement(si, 'SellerAccountDetails')
    said = SubElement(sa, 'SellerAccountID')
    said.set('IdentificationSchemeName', 'IBAN')
    said.text = expense.iban
    sab = SubElement(sa, 'SellerBic')
    sab.set('IdentificationSchemeName', 'BIC')
    sab.text = expense.swift_bic

    b = SubElement(top, 'BuyerPartyDetails')
    bpi = SubElement(b, 'BuyerPartyIdentifier')
    bpi.text = expense.organisation.business_id
    bon = SubElement(b, 'BuyerOrganisationName')
    bon.text = expense.organisation.name

    i = SubElement(top, 'InvoiceDetails')
    itc = SubElement(i, 'InvoiceTypeCode')
    itc.text = 'INV01'
    itt = SubElement(i, 'InvoiceTypeText')
    itt.text = 'LASKU'
    i_n = SubElement(i, 'OriginCode')
    i_n.text = 'Original'
    i_n = SubElement(i, 'InvoiceNumber')
    i_n.text = str(expense.id)
    i_d = SubElement(i, 'InvoiceDate')
    i_d.set('Format', 'CCYYMMDD')
    i_d.text = expense.created_at.strftime('%Y%m%d')

    if expense.needsKatre():
        i_ref = SubElement(i, 'BuyerReferenceIdentifier')
        i_ref.text = 'KATRE_EMCE'

    itvea = SubElement(i, 'InvoiceTotalVatExcludedAmount')
    itvea.set('AmountCurrencyIdentifier', 'EUR')
    itvea.text = currency(expense.amount(), '')
    itvva = SubElement(i, 'InvoiceTotalVatAmount')
    itvva.set('AmountCurrencyIdentifier', 'EUR')
    itvva.text = '0'
    itvia = SubElement(i, 'InvoiceTotalVatIncludedAmount')
    itvia.set('AmountCurrencyIdentifier', 'EUR')
    itvia.text = currency(expense.amount(), '')
    iv = SubElement(i, 'VatSpecificationDetails')
    ivba = SubElement(iv, 'VatBaseAmount')
    ivba.set('AmountCurrencyIdentifier', 'EUR')
    ivba.text = currency(expense.amount(), '')
    ivrp = SubElement(iv, 'VatRatePercent')
    ivrp.text = '0'
    ivra = SubElement(iv, 'VatRateAmount')
    ivra.set('AmountCurrencyIdentifier', 'EUR')
    ivra.text = '0'
    iftd = SubElement(i, 'InvoiceFreeText')
    iftd.text = expense.description
    # iftm = SubElement(i, 'InvoiceFreeText')
    # iftm.text = expense.memo

    for line in expenselines:
        row = SubElement(top, 'InvoiceRow')
        ran = SubElement(row, 'ArticleName')
        ran.text = line.expensetype.name + ': ' + line.description
        raq = SubElement(row, 'DeliveredQuantity')
        raq.set('QuantityUnitCode', line.expensetype.unit)
        raq.text = currency(line.basis, '')
        raa = SubElement(row, 'UnitPriceAmount')
        raa.set('AmountCurrencyIdentifier', 'EUR')
        raa.text = currency(line.expensetype.multiplier, '')
        ra = SubElement(row, 'RowShortProposedAccountIdentifier')
        ra.text = line.expensetype.account
        rd = SubElement(row, 'RowAccountDimensionText')
        if line.accountdimension:
            rd.text = line.accountdimension.code
        rvva = SubElement(row, 'RowVatRatePercent')
        rvva.text = '0'
        rvva = SubElement(row, 'RowVatAmount')
        rvva.set('AmountCurrencyIdentifier', 'EUR')
        rvva.text = '0'
        rvea = SubElement(row, 'RowVatExcludedAmount')
        rvea.set('AmountCurrencyIdentifier', 'EUR')
        rvea.text = currency(line.sum(), '')
        rva = SubElement(row, 'RowAmount')
        rva.set('AmountCurrencyIdentifier', 'EUR')
        rva.text = currency(line.sum(), '')

        # Nyt jännittää -Joonas
        # 10.1.2013 - Added if-statements to verify that the values actually exist
        if line.begin_at:
            rsd = SubElement(row, 'StartDate')
            rsd.set('Format', 'CCYYMMDD')
            rsd.text = line.begin_at.strftime('%Y%m%d')
        if line.ended_at:
            red = SubElement(row, 'EndDate')
            red.set('Format', 'CCYYMMDD')
            red.text = line.ended_at.strftime('%Y%m%d')

        if line.expensetype.requires_endtime:
            rft = SubElement(i, 'InvoiceFreeText')
            rft.text = (line.expensetype.name + ', ' +
                        line.description +
                        ': ' +
                        timezone.localtime(line.begin_at).strftime('%d.%m.%Y %H:%M') +
                        ' - ' +
                        timezone.localtime(line.ended_at).strftime('%d.%m.%Y %H:%M'))

    e = SubElement(top, 'EpiDetails')
    ei = SubElement(e, 'EpiIdentificationDetails')
    eid = SubElement(ei, 'EpiDate')
    eid.set('Format', 'CCYYMMDD')
    eid.text = expense.created_at.strftime('%Y%m%d')
    SubElement(ei, 'EpiReference')
    ep = SubElement(e, 'EpiPartyDetails')
    epb = SubElement(ep, 'EpiBfiPartyDetails')
    epbi = SubElement(epb, 'EpiBfiIdentifier')
    epbi.set('IdentificationSchemeName', 'BIC')
    epbi.text = expense.swift_bic
    epd = SubElement(ep, 'EpiBeneficiaryPartyDetails')
    epdn = SubElement(epd, 'EpiNameAddressDetails')
    epdn.text = expense.name
    epda = SubElement(epd, 'EpiAccountID')
    epda.set('IdentificationSchemeName', 'IBAN')
    epda.text = expense.iban
    ey = SubElement(e, 'EpiPaymentInstructionDetails')
    er = SubElement(ey, 'EpiRemittanceInfoIdentifier')
    er.set('IdentificationSchemeName', 'SPY')
    refno = str(expense.created_at.strftime('%Y')) + str(expense.id).zfill(5)
    from expenseapp.helpers import viitenumeron_tarkiste
    er.text = refno + str(viitenumeron_tarkiste(refno))
    eya = SubElement(ey, 'EpiInstructedAmount')
    eya.set('AmountCurrencyIdentifier', 'EUR')
    eya.text = currency(expense.amount(), '')
    ec = SubElement(ey, 'EpiCharge')
    ec.set('ChargeOption', 'SHA')
    eyd = SubElement(ey, 'EpiDateOptionDate')
    eyd.set('Format', 'CCYYMMDD')
    eyd.text = expense.created_at.strftime('%Y%m%d')

    return tostring(top.getroottree(), encoding='UTF-8', xml_declaration=True, pretty_print=True)
