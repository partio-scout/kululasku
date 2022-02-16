from http.client import HTTPResponse
import logging
from functools import partial
from turtle import title

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ExpenseForm, ExpenseLineForm, PersonForm, OrganisationForm
from .models import Expense, ExpenseLine, ExpenseType, Organisation, Person
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from collections import OrderedDict
from collections import deque
from django.urls import reverse
from django.contrib import messages
from os.path import basename
from django.utils.encoding import smart_text
from expenseapp.helpers import cc_expense
from datetime import datetime
from .helpers import decimal_in_r82
from decimal import Decimal
from django.utils import translation


def language_activate(request, lang):
    languages = {
        'fi': 'fi-FI',
        'sv': 'sv-SE',
        'en': 'en-EN',
    }
    response = redirect('/expense/')

    if lang in languages:
        language = languages.get(lang)
        response.set_cookie('django_language', language)
        translation.activate(language)
    return response


@login_required()
def receipt_fetch(request, expenselineid):
    expenseline = get_object_or_404(ExpenseLine, pk=expenselineid)
    if not (expenseline.expense.user == request.user or request.user.has_perm('expenseapp.change_expense')):
        return redirect('/accounts/login/?next=%s' % request.path)

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_text(
        basename(expenseline.receipt.name))
    response['X-Accel-Redirect'] = expenseline.receipt.url
    return response


@login_required()
def organisationselection(request):
    organisations = Organisation.objects.filter(active=True).order_by('name')
    orgs = []

    for organisation in organisations:
        if request.user.person.type:
            types = ExpenseType.objects.filter(
                organisation=organisation, persontype=request.user.person.type)
        else:
            types = ExpenseType.objects.filter(organisation=organisation)
        if types.exists():
            orgs.append(organisation)

    return render(request, 'organisationselection.html', {
        'page_title': _('Select your organisation to continue'),
        'organisations': orgs,
    })


@login_required()
def ownexpenses(request):
    expenses = Expense.objects.filter(
        user=request.user).order_by('-created_at')

    list = deque()
    for expense in expenses:
        list.append(expense)

    return render(request, 'ownexpenses.html', {
        'page_title': _('My expenses'),
        'expenses': list,
    })


@login_required()
def expense(request, organisation_id):
    organisation = Organisation.objects.filter(id=organisation_id).first()
    if not (organisation.active == True or request.user.has_perm('expenseapp.change_expense')):
        return redirect('/accounts/login/?next=%s' % request.path)
    try:
        initial = {
            'organisation': organisation_id,
            'name': request.user.person.name(),
            'email': request.user.email,
            'address': request.user.person.address,
            'personno': request.user.person.personno,
            'iban': request.user.person.iban,
            'swift_bic': request.user.person.swift_bic,
            'phone': request.user.person.phone,
            'user': request.user.id,
        }
    except Exception as e:
        messages.error(request, _(
            'Please verify your personal information is correct.'))

    expense_form = ExpenseForm((request.POST or None),
                               (request.FILES or None),
                               prefix='expenseform',
                               initial=initial)

    preview_mode = request.POST.get('preview', "0")
    if preview_mode == "1":
        if expense_form.is_valid():
            expense = Expense()
            expense.organisation = organisation
            expense.user = request.user

            fields = OrderedDict()
            fields['name'] = {'label': _(
                'Applicant Name'),            'value': expense_form.cleaned_data['name'], }
            fields['email'] = {'label': _(
                'Email'),           'value': expense_form.cleaned_data['email'], }
            fields['phone'] = {'label': _(
                'Phone'),           'value': expense_form.cleaned_data['phone'], }
            fields['address'] = {'label': _(
                'Address'),         'value': expense_form.cleaned_data['address'], }
            fields['iban'] = {'label': _(
                'Bank account no'), 'value': expense_form.cleaned_data['iban'], }
            fields['swift_bic'] = {'label': _(
                'BIC no'),          'value': expense_form.cleaned_data['swift_bic'], }
            fields['personno'] = {'label': _(
                'Person number'),   'value': expense_form.cleaned_data['personno'], }
            fields['description'] = {'label': _(
                'Description'),     'value': expense_form.cleaned_data['description'], }
            fields['memo'] = {'label': _(
                'Info'),            'value': expense_form.cleaned_data['memo'], }
            fields['date'] = {'label': _('Sent'),
                              'value': datetime.now(), }

            total_sum = 0
            lines = []
            num_lines = int(request.POST.get(
                'expenseform_EXPENSELINES-TOTAL_FORMS'))
            for line_num in range(num_lines):
                line_prefix = "expenseform_EXPENSELINES-%s-" % line_num
                tmp = OrderedDict()
                line = ExpenseLine()
                try:
                    line.basis = Decimal(request.POST.get(
                        "%sbasis" % line_prefix).replace(",", "."))
                    line.expensetype = ExpenseType.objects.get(
                        pk=request.POST.get("%sexpensetype" % line_prefix))
                    ended_at_date_input = request.POST.get(
                        "%sended_at_date" % line_prefix, None)
                    ended_at_time_input = request.POST.get(
                        "%sended_at_time" % line_prefix, None)
                    begin_at_date_input = request.POST.get(
                        "%sbegin_at_date" % line_prefix, None)
                    begin_at_time_input = request.POST.get(
                        "%sbegin_at_time" % line_prefix, None)
                except Exception as e:
                    messages.error(request, _(
                        'Please verify that all information is correct.'))

                try:
                    line_receipt = request.FILES.get("%sreceipt" % line_prefix)
                    if line_receipt:
                        tmp['receipt'] = {'label': _(
                            'Receipt'), 'url': None, 'filename': line_receipt.name}
                except Exception as e:
                    messages.error(request, _('Please verify the given file.'))

                if(line.expensetype.requires_endtime):
                    try:
                        if(ended_at_time_input == ''):
                            ended_at_time_str = "00.00"
                            ended_at_str = '%s %s' % (
                                ended_at_date_input, ended_at_time_str)
                            ended_at = datetime.strptime(
                                ended_at_str, "%d.%m.%Y %H.%M")
                        else:
                            ended_at_str = '%s %s' % (
                                ended_at_date_input, ended_at_time_input)
                            ended_at = datetime.strptime(
                                ended_at_str, "%d.%m.%Y %H.%M")
                    except Exception as e:
                        messages.error(request, _(
                            'Please verify ending dates are correct.'))
                else:
                    ended_at = None

                if(line.expensetype.requires_start_time):
                    try:
                        if(begin_at_date_input == ''):
                            return HttpResponse("<script>window.top.$('#id_preview').val(0); window.top.$('#expense-form').off('submit.open_preview').attr('target', '').submit();</script>")
                        else:
                            if(begin_at_time_input == ''):
                                begin_at_time_input = "00.00"
                        begin_at_str = '%s %s' % (
                            begin_at_date_input, begin_at_time_input)
                        begin_at = datetime.strptime(
                            begin_at_str, "%d.%m.%Y %H.%M")
                    except Exception as e:
                        messages.error(request, _(
                            'Please verify dates are correct.'))
                else:
                    begin_at_time_input = "00.00"
                    begin_at_str = '%s %s' % (
                        begin_at_date_input, begin_at_time_input)
                    begin_at = datetime.strptime(
                        begin_at_str, "%d.%m.%Y %H.%M")

                expense_form.cleaned_data['expenseform_EXPENSELINES-0-begin_at'] = begin_at

                tmp['id'] = None
                tmp['begin_at'] = {'label': _(
                    'Begin at'),      'value': begin_at}
                tmp['ended_at'] = {'label': _(
                    'Ended at'),      'value': ended_at}
                tmp['description'] = {'label': _('Description'),   'value': request.POST.get(
                    "%sdescription" % line_prefix)}
                tmp['basis'] = {'label': _('Amount'),
                                'value': line.basis}
                tmp['expensetype'] = {'label': _(
                    'Expense type'),  'value': line.expensetype}
                tmp['sum'] = {'label': _('Sum'),
                              'value': line.sum(), }
                total_sum += line.sum()

                lines.append(tmp)

            fields['total'] = {'label': _(
                'Total'),           'value': total_sum}
            messages.info(request, _(
                "Please verify that all information is correct before submitting the application for review"))
            return render(request, 'showexpense_preview.html', {
                'page_title': f'{_("Expense for")} {expense.organisation.name}',
                'expense': expense,
                'fields': fields,
                'lines': lines,
            })
        else:
            # If the form is not valid, we clear the form target and submit it again so we get proper form validation errors
            return HttpResponse("<script>window.top.$('#id_preview').val(0); window.top.$('#expense-form').off('submit.open_preview').attr('target', '').submit();</script>")

    ### For debugging ###
    # import time
    # time.sleep(5)
    if expense_form.is_valid():
        expense = expense_form.save()
        # Send the email
        cc_expense(expense)
        messages.success(request, _('Expense information saved.'))
        return HttpResponseRedirect(reverse('expense_view', kwargs={'expense_id': expense.id}))
        # return render(request, 'expense.html', {
        #     'page_title': _("Expense for"),
        #     'exp_form': expense_form,
        #     'organisation': organisation,
        #     'expense_id': expense.id
        # })
    return render(request, 'expense.html', {
        'page_title': _("Expense for"),
        'exp_form': expense_form,
        'organisation': organisation,
    })


@login_required()
def showexpense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)

    if not (request.user == expense.user or request.user.has_perm('expenseapp.change_expense')):
        return redirect('/accounts/login/?next=%s' % request.path)

    fields = OrderedDict()
    fields['name'] = {'label': _('Name'), 'value': expense.name, }
    fields['email'] = {'label': _('Email'), 'value': expense.email, }
    fields['phone'] = {'label': _('Phone'), 'value': expense.phone, }
    fields['address'] = {'label': _('Address'), 'value': expense.address, }
    fields['iban'] = {'label': _('Bank account no'), 'value': expense.iban, }
    fields['swift_bic'] = {'label': _('BIC no'), 'value': expense.swift_bic, }
    fields['personno'] = {'label': _(
        'Person number'), 'value': expense.personno, }
    fields['description'] = {'label': _(
        'Description'), 'value': expense.description, }
    fields['memo'] = {'label': _('Info'), 'value': expense.memo, }
    fields['date'] = {'label': _('Sent'), 'value': expense.created_at, }
    fields['total'] = {'label': _('Total'), 'value': expense.amount(), }

    lines = []

    res = ExpenseLine.objects.filter(expense=expense)
    for line in res:
        tmp = OrderedDict()
        tmp['id'] = line.id
        tmp['begin_at'] = {'label': _('Begin at'), 'value': line.begin_at, }
        tmp['ended_at'] = {'label': _('Ended at'), 'value': line.ended_at, }
        tmp['description'] = {'label': _(
            'Description'), 'value': line.description, }
        tmp['basis'] = {'label': _('Amount'), 'value': line.basis, }
        tmp['expensetype'] = {'label': _(
            'Expense type'), 'value': line.expensetype, }
        tmp['sum'] = {'label': _('Sum'), 'value': line.sum(), }

        if line.receipt:
            tmp['receipt'] = {'label': _(
                'Receipt'), 'url': line.receipt, 'filename': line.receipt.name.split('/')[-1]}

        lines.append(tmp)

    return render(request, 'showexpense.html', {
        'page_title': f'{_("Expense for")} {expense.organisation.name}',
        'expense': expense,
        'fields': fields,
        'lines': lines,
    })


@login_required()
def xmlexpense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)

    if not (request.user == expense.user or request.user.has_perm('expenseapp.change_expense')):
        return redirect('/accounts/login/?next=%s' % request.path)

    return HttpResponse(expense.finvoice(), content_type="text/xml")


@login_required()
def katreexpense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)

    if not (request.user == expense.user or request.user.has_perm('expenseapp.change_expense')):
        return redirect('/accounts/login/?next=%s' % request.path)

    return HttpResponse(expense.katre(), content_type="text/xml")


@login_required()
def personinfo(request):

    person, created = Person.objects.get_or_create(user=request.user)
    initial = {
        'firstname': request.user.first_name,
        'lastname': request.user.last_name,
        'email': request.user.email,
    }
    form = PersonForm((request.POST or None), instance=person, initial=initial)

    if form.is_valid():
        form.save()
        user = User.objects.get(id=request.user.id)
        user.first_name = form.cleaned_data['firstname']
        user.last_name = form.cleaned_data['lastname']
        user.email = form.cleaned_data['email']
        user.save()

        messages.success(request, _('Profile details updated.'))
    elif form.errors:
        messages.error(request, _(
            'Please verify that all information is correct.'))

    # Get any organisations the user has admin privileges for
    organisations = Organisation.objects.all().order_by('name')
    orgs = []
    for org in organisations:
        if request.user.has_perm('expenseapp.change_organisation_' + str(org.id)):
            orgs.append(org)

    return render(request, 'personinfo.html', {
        'page_title': 'Muokkaa tietojasi',
        'form': form,
        'orgs': orgs,
    })


def organisationedit(request, organisation_id):
    if not request.user.has_perm('expenseapp.change_organisation_' + str(organisation_id)):
        return redirect('/login/?next=%s' % request.path)

    organisation = get_object_or_404(Organisation, pk=organisation_id)

    years = []
    years_raw = Expense.objects.filter(
        organisation=organisation).datetimes('created_at', 'year')
    for year in years_raw:
        years.append(year.strftime('%Y'))

    form = OrganisationForm((request.POST or None),
                            prefix='organisationform',
                            instance=organisation)

    if form.is_valid():
        form.save()
        messages.success(request, _('Organisation details updated.'))
        return HttpResponseRedirect(reverse('organisation_edit', kwargs={'organisation_id': organisation.id}))

    return render(request, 'organisationedit.html', {
        'page_title': 'Muokkaa organisaatiota',
        'form': form,
        'years': years,
        'orgid': organisation_id,
    })


def annualreport(request, organisation_id, year):
    if not request.user.has_perm('expenseapp.change_organisation_' + str(organisation_id)):
        return redirect('/login/?next=%s' % request.path)

    output = ''
    i = 1

    now = datetime.now()
    timestamp = now.strftime("%d%m%Y%H%M%S")  # PPKKVVVVHHMMSS

    organisation = get_object_or_404(Organisation, pk=organisation_id)
    expenses = Expense.objects.filter(
        organisation=organisation, created_at__year=year).order_by('personno')

    persons = {}

    # Aggregate all needed data per-person
    for expense in expenses:
        if not expense.personno in persons:
            persons[expense.personno] = {
                'fpd': 0, 'ppd': 0, 'fopd': 0, 'ma': 0, 'km': 0, 'kmamount': 0, 'amount': 0}
        lines = ExpenseLine.objects.filter(expense=expense)
        for line in lines:
            if line.expensetype_type in ['FPD', 'PPD', 'FOPD', 'MA']:
                persons[expense.personno]['amount'] += line.sum()
            if line.expensetype_type == 'T':
                persons[expense.personno]['km'] += line.basis
                persons[expense.personno]['kmamount'] += line.sum()
            elif line.expensetype_type == 'FPD':
                persons[expense.personno]['fpd'] = 1
            elif line.expensetype_type == 'PPD':
                persons[expense.personno]['ppd'] = 1
            elif line.expensetype_type == 'FOPD':
                persons[expense.personno]['fopd'] = 1
            elif line.expensetype_type == 'MA':
                persons[expense.personno]['da'] = 1

    # Output the above-aggregated data per-person
    for key, value in list(persons.items()):
        format = """000:VSPSKUST
084:H5
058:%s
010:%s
083:%s
150:%s
151:%s
152:%s
153:%s
154:%s
155:%s
156:%s
048:kululasku.partio.fi
014:2202642-0_KL
198:%s
999:%s
"""
        output += format % (year, organisation.business_id, key.upper(), decimal_in_r82(
            value['amount']), value['fpd'], value['ppd'], value['fopd'], value['ma'], int(value['km']), decimal_in_r82(value['kmamount']), timestamp, i)
        i = i+1

    # Output the organisation details
    format = """000:VSPSVYHT
058:%s
010:%s
041:%s
042:%s
048:kululasku.partio.fi
014:2202642-0_KL
198:%s
999:%s
"""
    output += format % (year, organisation.business_id, request.user.last_name.upper() +
                        ', ' + request.user.first_name.upper(), request.user.person.phone, timestamp, i)

    resp = HttpResponse(output, content_type="text/plain")
    resp['Content-Disposition'] = 'attachment; filename=annual_report_' + year + '.dat'
    return resp
