# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator, validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.admin import DateFieldListFilter
from django_registration.signals import user_registered
from django.utils.translation import gettext_lazy
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timezone
from localflavor.generic.models import IBANField, BICField


from .finvoice import createFinvoice
from .katre import createKatreReport


def validate_hetu(value):
    from stdnum.fi.hetu import validate
    from stdnum.exceptions import InvalidChecksum, InvalidFormat

    try:
        validate(value)
    except InvalidChecksum:
        raise ValidationError(gettext_lazy(
            'Enter a valid Finnish personal identity code.'))
    except InvalidFormat:
        pass
    except Exception as e:
        raise ValidationError(gettext_lazy(
            'Enter a valid Finnish personal identity code or Finnish business ID.'))


def validate_hetu_or_businessid(value):
    from stdnum.fi import hetu
    from stdnum.fi import ytunnus
    from stdnum.exceptions import InvalidChecksum, InvalidFormat

    errors = True

    try:
        hetu.validate(value)
        errors = False
    except (InvalidChecksum, InvalidFormat):
        pass
    except Exception as e:
        raise ValidationError(gettext_lazy(
            'Enter a valid Finnish personal identity code or Finnish business ID.'))

    try:
        ytunnus.validate(value)
        errors = False
    except:
        pass

    if errors:
        raise ValidationError(gettext_lazy(
            'Enter a valid Finnish personal identity code or Finnish business ID.'))


validators = {
    'personno': [
        RegexValidator(r'^[0-3][0-9][0-1][0-9][0-9]{2}[-A+][0-8][0-9]{2}[0-9a-zA-Z]$',
                       gettext_lazy('Enter a valid Finnish personal identity code.')),
        validate_hetu,
    ],
    'businessid': [
        RegexValidator(r'^[0-9]{1,7}-[0-9]$',
                       gettext_lazy('Enter a valid Finnish business ID.')),
    ],
    'hetu_or_businessid': [
        validate_hetu_or_businessid,
    ],
    'address': [
        # Lyhin kadunnimi on Itu => lyhin katuosoite Itu 1
        MinLengthValidator(5),
        MaxLengthValidator(255),
    ],
    'phoneno': [
        RegexValidator(r'^\+?[0-9]{7,13}',
                       gettext_lazy('Enter a valid phone number without any spaces or dashes.')),
    ],
    'email': [
        validate_email,
    ],
    'name': [
        RegexValidator(r'^\S+( \S+)+$',
                       gettext_lazy('Enter your first and last name.')),
        MinLengthValidator(6),
        MaxLengthValidator(255),
    ],
}


class InfoMessage(models.Model):
    app_label = 'expenseapp'
    title_fi = models.CharField("Otsikko", max_length=200, blank=True)
    description_fi = models.TextField(
        gettext_lazy("Selite"), max_length=2000, blank=True)

    title_se = models.CharField("Rubrik", max_length=200, blank=True)
    description_se = models.TextField(
        'Förklaring', max_length=2000, blank=True)

    title_en = models.CharField("Title", max_length=200, blank=True)
    description_en = models.TextField("Content", max_length=2000, blank=True)

    start_date = models.DateTimeField(
        gettext_lazy('Näkyvissä alkaen'), blank=True)
    end_date = models.DateTimeField(
        gettext_lazy('Päättyy'), blank=True)
    created_at = models.DateTimeField(gettext_lazy('Sent'), auto_now_add=True)
    updated_at = models.DateTimeField(gettext_lazy('Edited'), auto_now=True)

    def __str__(self):
        return self.title_fi

    def languaged(self, LANGUAGE_CODE):
        copy = self
        copy.title = self.title(LANGUAGE_CODE)
        copy.description = self.description(LANGUAGE_CODE)
        return copy

    def title(self, LANGUAGE_CODE):
        if LANGUAGE_CODE == 'fi-FI':
            if self.title_fi:
                return self.title_fi
            if self.title_en:
                return self.title_en
            return self.title_se

        if LANGUAGE_CODE == 'sv-SE':
            if self.title_se:
                return self.title_se
            if self.title_fi:
                return self.title_fi
            return self.title_en

        if LANGUAGE_CODE == 'en-EN':
            if self.title_en:
                return self.title_en
            if self.title_fi:
                return self.title_fi
            return self.title_se
        return self.title_fi

    def description(self, LANGUAGE_CODE):
        if LANGUAGE_CODE == 'fi-FI':
            if self.description_fi:
                return self.description_fi
            if self.description_en:
                return self.description_en
            return self.description_se

        if LANGUAGE_CODE == 'sv-SE':
            if self.description_se:
                return self.description_se
            if self.description_fi:
                return self.description_fi
            return self.description_en

        if LANGUAGE_CODE == 'en-EN':
            if self.description_en:
                return self.description_en
            if self.description_fi:
                return self.description_fi
            return self.description_se
        return self.description_fi

    class Meta:
        verbose_name = "Tiedoksianto"
        verbose_name_plural = "Tiedoksiannot"


class InfoMessageAdmin(admin.ModelAdmin):
    readonly_fields = ('status',)
    fields = ('title_fi', 'title_se', 'title_en',
              'description_fi', 'description_se', 'description_en',
              'start_date', 'end_date')
    list_display = ['status', 'title_fi', 'title_se',
                    'title_en', 'start_date', 'end_date', 'id']
    search_fields = ('title_fi', 'description_fi')
    ordering = ('title_fi', 'title_se', 'title_en',
                'description_fi', 'description_se', 'description_en',
                'start_date', 'end_date')

    def status(self, obj):
        now = datetime.now(timezone.utc)
        return 'Näkyy sivuilla' if (now.isoformat() >= obj.start_date.isoformat()) and (now.isoformat() <= obj.end_date.isoformat()) else 'Ei näy'


class Organisation(models.Model):
    name = models.CharField(gettext_lazy('Name'), max_length=255)
    business_id = models.CharField(gettext_lazy(
        'Business ID'), max_length=9, validators=validators['businessid'])
    emce_id = models.CharField(gettext_lazy(
        'EmCe yritystunnus'), max_length=128, null=True, blank=True)
    katre_cert_business_id = models.CharField(gettext_lazy(
        'Katre-varmenteen Y-tunnus'), max_length=9, validators=validators['businessid'], null=True, blank=True)
    active = models.BooleanField(gettext_lazy('Selectable'))
    send_active = models.BooleanField(gettext_lazy('Send active'))
    # default=None
    default_expense_type = models.ForeignKey(
        'ExpenseType', null=True, default=None, blank=True, related_name="+", on_delete=models.SET_DEFAULT)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organisaatio"
        verbose_name_plural = " Organisaatiot"


def organisation_edited(sender, instance, created, **kwargs):
    codename = 'change_organisation_' + str(instance.id)
    if not Permission.objects.filter(codename=codename):
        Permission.objects.create(content_type=ContentType.objects.get(app_label="expenseapp", model="organisation"),
                                  codename=codename, name="Change %s" % instance.name)


post_save.connect(organisation_edited, sender=Organisation)


class AccountDimension(models.Model):
    name = models.CharField(gettext_lazy('Name'), max_length=255)
    code = models.CharField(gettext_lazy('Account dimension code'), max_length=5, help_text=gettext_lazy(
        'Account dimension code(s). If multiple, separate with semicolons (;).'))

    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Kustannuspaikan koodi'
        verbose_name_plural = 'Kustannuspaikat'


class AccountDimensionInline(admin.TabularInline):
    model = AccountDimension
    extra = 0
    can_delete = False
    fields = ('name', 'code',)


PERSONTYPE_CHOICES = (
    (1, gettext_lazy('Trustee')),
    (2, gettext_lazy('Employee')),
)


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)

    phone = models.CharField(gettext_lazy(
        'Phone'), max_length=255, blank=True, null=True, validators=validators['phoneno'])
    address = models.CharField(gettext_lazy(
        'Address'), max_length=255, blank=True, null=True, validators=validators['address'])
    iban = IBANField(gettext_lazy('Bank account no'), blank=True, null=True)
    swift_bic = BICField(gettext_lazy('BIC no'), blank=True, null=True)
    personno = models.CharField(gettext_lazy('Person number'), max_length=11, blank=True, null=True, validators=validators['hetu_or_businessid'], help_text=gettext_lazy(
        'Person number is required for every expense application for annual announcements to the tax authority. If you don\'t want to save it here, you can enter it to each expense application separately.'))
    type = models.IntegerField(gettext_lazy(
        'Type'), choices=PERSONTYPE_CHOICES, default=1)
    language = models.CharField(gettext_lazy(
        'Site language'), max_length=6, blank=True, null=True, choices=settings.LANGUAGES)

    def name(self):
        return self.user.first_name + ' ' + self.user.last_name

    def __unicode__(self):
        return f'{self.name()} – {self.user.email}'

    class Meta:
        verbose_name_plural = "Henkilötiedot"  # 2 spaces


def createPerson(sender, user, request, **kwargs):
    Person.objects.get_or_create(user=user)


user_registered.connect(createPerson)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', '__unicode__', 'type')
    list_filter = ('type', )
    search_fields = ('type',)
    actions = ['set_type']

    def set_type(self, request, queryset):
        queryset.update(type=1)
    set_type.short_description = "Vaihda luottamushenkilöksi"


class PersonInline(admin.StackedInline):
    model = Person
    can_delete = False
    verbose_name_plural = 'person'


EXPENSE_TYPES = (
    ('T', gettext_lazy('Mileage')),
    ('FPD', gettext_lazy('Full per diem')),
    ('PPD', gettext_lazy('Partial per diem')),
    ('FOPD', gettext_lazy('Foreign per diem')),
    ('MA', gettext_lazy('Meal allowance')),
    ('O', gettext_lazy('Other')),
)

UNITS = (
    ('km', gettext_lazy('km')),
    ('d', gettext_lazy('days')),
    ('pcs', gettext_lazy('pieces')),
    ('EUR', gettext_lazy('€')),
)


class ExpenseType(models.Model):
    name = models.CharField(gettext_lazy('Name'), max_length=255)
    active = models.BooleanField(gettext_lazy('Active'), default=True)
    type = models.CharField(gettext_lazy(
        'Type'), max_length=5, choices=EXPENSE_TYPES)
    requires_receipt = models.BooleanField(
        gettext_lazy('Requires receipt'), default=False)
    multiplier = models.DecimalField(gettext_lazy('Multiplier'), max_digits=10, decimal_places=2, help_text=gettext_lazy(
        'The per price for the expense type (mileage: € per km, other expenses: 1, advances: -1)'))
    requires_endtime = models.BooleanField(gettext_lazy(
        'Requires ending date and time'), default=False)
    requires_start_time = models.BooleanField(
        gettext_lazy('Requires starting time'), default=False)
    persontype = models.IntegerField(gettext_lazy(
        'Person type'), null=True, default=None, blank=True, choices=PERSONTYPE_CHOICES)
    account = models.CharField(gettext_lazy('Account'), max_length=20)
    unit = models.CharField(gettext_lazy('Unit'), max_length=5, choices=UNITS)

    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '%s' % self.name

    def js_data(self):
        return {
            'name': self.name,
            'multiplier': str(self.multiplier),
            'unit': self.unit,
            'requires_endtime': self.requires_endtime,
            'requires_start_time': self.requires_start_time,
            'basis_text': str(gettext_lazy('HUOM. Lisää matkareitti ja matkustajat')) if self.type == 'T' else ''
        }

    def __unicode__(self):
        if self.requires_receipt:
            return self.name + ' (' + gettext_lazy('Requires receipt') + ')'
        if self.requires_endtime:
            return self.name + ' (' + gettext_lazy('Requires ending time') + ')'
        if self.requires_start_time:
            return self.name + ' (' + gettext_lazy('Requires starting time') + ')'

        return self.name

    class Meta:
        ordering = ('organisation', 'name')


class ExpenseTypeInline(admin.TabularInline):
    model = ExpenseType
    extra = 0
    can_delete = False
    fields = ('name', 'active', 'type', 'persontype', 'multiplier', 'requires_receipt',
              'requires_endtime', 'requires_start_time', 'account', 'unit',)
    list_filter = (
        ('default_expense_type', admin.RelatedOnlyFieldListFilter),
    )

    def __unicode__(self):
        return f'{self.name} 2'


class OrganisationAdmin(admin.ModelAdmin):
    ordering = ['name']
    inlines = [
        ExpenseTypeInline,
        AccountDimensionInline,
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        organisation_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "default_expense_type":
            kwargs["queryset"] = ExpenseType.objects.filter(
                organisation=organisation_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


APPLICATION_STATUSES = (
    (0, gettext_lazy('Open')),
    (1, gettext_lazy('Sent')),
)

KATRE_STATUSES = (
    (0, gettext_lazy('Open')),
    (1, gettext_lazy('Not needed')),
    (2, gettext_lazy('Sent')),
)


class Expense(models.Model):
    name = models.CharField(gettext_lazy(
        'Name'), max_length=255, validators=validators['name'])
    email = models.EmailField(gettext_lazy(
        'Email address'), validators=validators['email'])
    cc_email = models.EmailField(gettext_lazy('CC email address'), blank=True, null=True, help_text=gettext_lazy(
        'Copy of the expense will be sent to the email.'), validators=validators['email'])
    phone = models.CharField(gettext_lazy(
        'Phone'), max_length=255, validators=validators['phoneno'])
    address = models.CharField(gettext_lazy(
        'Address'), max_length=255, validators=validators['address'])
    iban = IBANField(gettext_lazy('Bank account no'))
    swift_bic = BICField(gettext_lazy('BIC no'), blank=True, null=True)
    personno = models.CharField(gettext_lazy('Person number'), max_length=11, validators=validators['hetu_or_businessid'], help_text=gettext_lazy(
        'If you apply for an expense reimbursement for a local group, enter the group’s business ID here. Kilometric allowances and daily subsistence allowances can not be applied for with a business ID.'))
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    description = models.CharField(gettext_lazy('Purpose'), help_text=gettext_lazy(
        'Eg. Names of the additional passengers, people in the meeting, cost centre or activity sector.'), max_length=255)
    memo = models.TextField(gettext_lazy('Info'), help_text=gettext_lazy(
        'Eg. Names of the additional passengers, people in the meeting, cost centre or activity sector.'), blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)
    status = models.IntegerField(gettext_lazy(
        'Status'), choices=APPLICATION_STATUSES, default=0)
    katre_status = models.IntegerField(gettext_lazy(
        'Katre status'), choices=KATRE_STATUSES, default=0)

    created_at = models.DateTimeField(gettext_lazy('Sent'), auto_now_add=True)
    updated_at = models.DateTimeField(gettext_lazy('Edited'), auto_now=True)

    def amount(self):
        sum = 0
        lines = ExpenseLine.objects.filter(expense=self)
        for line in lines:
            sum += line.sum()
        return sum

    def __unicode__(self):
        return self.name + ': ' + self.description + ' (' + str(round(self.amount(), 2)) + ' €)'

    def __str__(self):
        return self.name + ': ' + self.description + ' (' + str(round(self.amount(), 2)) + ' €)'

    def finvoice(self):
        expense = self
        expenselines = ExpenseLine.objects.filter(expense=expense)

        return createFinvoice(expense, expenselines)

    def needsKatre(self):
        expense = self
        expenselines = ExpenseLine.objects.filter(expense=expense)

        for line in expenselines:
            if line.expensetype_type in ['FPD', 'PPD', 'FOPD', 'MA', 'T']:
                return True

        return False

    def katre(self):
        expense = self
        expenselines = ExpenseLine.objects.filter(expense=expense)

        return createKatreReport(expense, expenselines)

    class Meta:
        verbose_name_plural = "  Kululaskut"  # 2 spaces
        verbose_name = "Kululasku"


def receipt_path(path, filename):
    import os
    filename = str(filename.encode('ascii', 'ignore'))
    return os.path.join(path, filename)


class ExpenseLine(models.Model):
    description = models.CharField(gettext_lazy('Description'), max_length=255, help_text=gettext_lazy(
        'Description of the expense, eg. the route of the journey (travel expenses) or purpose of the purchased goods'))
    begin_at = models.DateTimeField(gettext_lazy('Begin at'))
    ended_at = models.DateTimeField(
        gettext_lazy('Ended at'), blank=True, null=True)

    expensetype = models.ForeignKey(ExpenseType, verbose_name=gettext_lazy(
        'Expense type'), on_delete=models.PROTECT)
    accountdimension = models.ForeignKey(AccountDimension, verbose_name=gettext_lazy(
        'Cost centre'), blank=True, null=True, on_delete=models.PROTECT)
    basis = models.DecimalField(gettext_lazy('Amount'), max_digits=10, decimal_places=2, help_text=gettext_lazy(
        'Amount of kilometres, days or the sum of the expense'))
    expense = models.ForeignKey(Expense, on_delete=models.PROTECT)

    receipt = models.FileField(gettext_lazy('Receipt'), upload_to='uploads/receipts', blank=True, null=True, help_text=gettext_lazy(
        'A scan or picture of the receipt. Accepted formats include PDF, PNG and JPG. Note: The receipt must clearly show what, when and how much has been paid!'))

    # These are in the ExpenseType too, but need to be duplicated to make sure that the data is retained after types are edited
    expensetype_name = models.CharField(gettext_lazy('Name'), max_length=255)
    expensetype_type = models.CharField(gettext_lazy(
        'Type'), max_length=5, choices=EXPENSE_TYPES)
    multiplier = models.DecimalField(gettext_lazy('Multiplier'), max_digits=10, decimal_places=2, help_text=gettext_lazy(
        'The per price for the expense type (mileage: € per km, other expenses: 1, advances: -1)'))

    def save(self):
        self.multiplier = self.expensetype.multiplier
        self.expensetype_type = self.expensetype.type
        self.expensetype_name = self.expensetype.name

        super(ExpenseLine, self).save()

    def sum(self):
        return self.basis * self.expensetype.multiplier

    def __unicode__(self):
        return self.description + ' (' + str(self.sum()) + ' e)'


class ExpenseLineInline(admin.TabularInline):
    model = ExpenseLine
    extra = 1
    fields = ('begin_at', 'ended_at', 'description',
              'expensetype', 'basis', 'receipt',)


def open_katre_again(modeladmin, request, queryset):
    for expense in queryset:
        expense.katre_status = 0
        expense.save()


open_katre_again.short_description = 'Siirrä Katre-ilmoitus avoimeksi'


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', '__unicode__', 'organisation',
                    'status', 'katre_status', 'created_at')
    list_filter = (
        'status',
        'organisation',
        'katre_status',
        'user__person__type',
        # ?date__gte=2009-5-1&date__lt=2009-8-1
        ('created_at', DateFieldListFilter),
    )
    search_fields = ('name', 'email', 'description')
    inlines = [
        ExpenseLineInline,
    ]
    readonly_fields = ('created_at',)
    actions = [open_katre_again, ]

    class Meta:
        verbose_name_plural = "Kululaskut"  # 2 spaces
        verbose_name = "Kululasku"  # 2 spaces
