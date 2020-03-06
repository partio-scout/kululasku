# -*- coding: utf-8 -*-

from django.db import models
from django.contrib import admin
from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator, validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.admin import DateFieldListFilter
from django_registration.signals import user_registered
from django.utils.translation import ugettext, ugettext_lazy
from locale import currency
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from localflavor.generic.models import IBANField, BICField
from django.template import defaultfilters
from django.utils import timezone

from .finvoice import createFinvoice
from .katre import createKatreReport

def validate_hetu(value):
  from stdnum.fi.hetu import is_valid, validate
  from stdnum.exceptions import InvalidChecksum, InvalidFormat

  try:
    validate(value)
  except InvalidChecksum:
    raise ValidationError(ugettext_lazy('Enter a valid Finnish personal identity code.'))
  except InvalidFormat:
    pass

def validate_hetu_or_businessid(value):
  import re
  from stdnum.fi.hetu import is_valid, validate
  from stdnum.exceptions import InvalidChecksum, InvalidFormat
  
  errors = True
  
  try:
    validate(value)
    errors = False
  except (InvalidChecksum, InvalidFormat):
    pass
  
  
  business_id_regex = re.compile(r'^[0-9]{1,7}-[0-9]$')
  is_valid_business_id = bool(business_id_regex.search(value))

  if is_valid_business_id:
    errors = False
    
  if errors:
    raise ValidationError(ugettext_lazy('Enter a valid Finnish personal identity code or Finnish business ID.'))


validators = {
  'personno': [
    RegexValidator(r'^[0-3][0-9][0-1][0-9][0-9]{2}[-A+][0-8][0-9]{2}[0-9a-zA-Z]$',
      ugettext_lazy('Enter a valid Finnish personal identity code.')),
    validate_hetu,
  ],
  'businessid': [
    RegexValidator(r'^[0-9]{1,7}-[0-9]$',
      ugettext_lazy('Enter a valid Finnish business ID.')),
  ],
  'hetu_or_businessid': [
    validate_hetu_or_businessid,
  ],
  'address': [
    MinLengthValidator(5), # Lyhin kadunnimi on Itu => lyhin katuosoite Itu 1
    MaxLengthValidator(255),
  ],
  'phoneno': [
    RegexValidator(r'^\+?[0-9]{7,13}',
     ugettext_lazy('Enter a valid phone number without any spaces or dashes.')),
  ],
  'email': [
    validate_email,
  ],
  'name': [
    RegexValidator(r'^\S+( \S+)+$', ugettext_lazy('Enter your first and last name.')),
    MinLengthValidator(6),
    MaxLengthValidator(255),
  ],
}


class Organisation(models.Model):
  name = models.CharField(ugettext_lazy('Name'), max_length=255)
  business_id = models.CharField(ugettext_lazy('Business ID'), max_length=9, validators=validators['businessid'])
  emce_id = models.CharField(ugettext_lazy('EmCe yritystunnus'), max_length=128, null=True, blank=True)
  katre_cert_business_id = models.CharField(ugettext_lazy('Katre-varmenteen Y-tunnus'), max_length=9, validators=validators['businessid'], null=True, blank=True)
  active = models.BooleanField(ugettext_lazy('Selectable'))
  send_active = models.BooleanField(ugettext_lazy('Send active'))
  # default=None
  default_expense_type = models.ForeignKey('ExpenseType', null=True, default=None, blank=True, related_name="+", on_delete=models.SET_DEFAULT)

  def __unicode__(self):
    return self.name
  
  def __str__(self):
        return self.name

def organisation_edited(sender, instance, created, **kwargs):
  codename = 'change_organisation_' + str(instance.id)
  if not Permission.objects.filter(codename=codename):
    Permission.objects.create(content_type=ContentType.objects.get(app_label="expenseapp", model="organisation"),
      codename=codename, name="Change %s" % instance.name)

post_save.connect(organisation_edited, sender=Organisation)

class AccountDimension(models.Model):
  name = models.CharField(ugettext_lazy('Name'), max_length=255)
  code = models.CharField(ugettext_lazy('Account dimension code'), max_length=5, help_text=ugettext_lazy('Account dimension code(s). If multiple, separate with semicolons (;).'))

  organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

  def __unicode__(self):
    return self.name

class AccountDimensionInline(admin.TabularInline):
  model = AccountDimension
  extra = 0
  can_delete = False
  fields = ('name', 'code',)

PERSONTYPE_CHOICES = (
  (1, ugettext_lazy('Trustee')),
  (2, ugettext_lazy('Employee')),
)

class Person(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)

  phone = models.CharField(ugettext_lazy('Phone'), max_length=255, blank=True, null=True, validators=validators['phoneno'])
  address = models.CharField(ugettext_lazy('Address'), max_length=255, blank=True, null=True, validators=validators['address'])
  iban = IBANField(ugettext_lazy('Bank account no'))
  swift_bic = BICField(ugettext_lazy('BIC no'), blank=True, null=True)
  personno = models.CharField(ugettext_lazy('Person number'), max_length=11, blank=True, null=True, validators=validators['hetu_or_businessid'], help_text=ugettext_lazy('Person number is required for every expense application for annual announcements to the tax authority. If you don\'t want to save it here, you can enter it to each expense application separately.'))
  type = models.IntegerField(ugettext_lazy('Type'), choices=PERSONTYPE_CHOICES, default=1)
  language = models.CharField(ugettext_lazy('Site language'), max_length=6, blank=True, null=True, choices=settings.LANGUAGES)

  def name(self):
    return self.user.first_name + ' ' + self.user.last_name

  def __unicode__(self):
    return self.name()

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
  ('T', ugettext_lazy('Mileage')),
  ('FPD', ugettext_lazy('Full per diem')),
  ('PPD', ugettext_lazy('Partial per diem')),
  ('FOPD', ugettext_lazy('Foreign per diem')),
  ('MA', ugettext_lazy('Meal allowance')),
  ('O', ugettext_lazy('Other')),
)

UNITS = (
  ('km', ugettext_lazy('km')),
  ('d', ugettext_lazy('days')),
  ('pcs', ugettext_lazy('pieces')),
  ('EUR', ugettext_lazy('€')),
)

class ExpenseType(models.Model):
  name = models.CharField(ugettext_lazy('Name'), max_length=255)
  active = models.BooleanField(ugettext_lazy('Active'), default=True)
  type = models.CharField(ugettext_lazy('Type'), max_length=5, choices=EXPENSE_TYPES)
  requires_receipt = models.BooleanField(ugettext_lazy('Requires receipt'), default=False)
  multiplier = models.DecimalField(ugettext_lazy('Multiplier'), max_digits=10, decimal_places=2, help_text=ugettext_lazy('The per price for the expense type (mileage: € per km, other expenses: 1, advances: -1)'))
  requires_endtime = models.BooleanField(ugettext_lazy('Requires ending date and time'), default=False)
  requires_start_time = models.BooleanField(ugettext_lazy('Requires starting time'), default=False)
  persontype = models.IntegerField(ugettext_lazy('Person type'), null=True, default=None, blank=True, choices=PERSONTYPE_CHOICES)
  account = models.CharField(ugettext_lazy('Account'), max_length=20)
  unit = models.CharField(ugettext_lazy('Unit'), max_length=5, choices=UNITS)

  organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

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
      'requires_start_time': self.requires_start_time
    }

  def __unicode__(self):
    if self.requires_receipt:
      return self.name + ' (' + ugettext('Requires receipt') + ')'
    if self.requires_endtime:
      return self.name + ' (' + ugettext('Requires ending time') + ')'
    if self.requires_start_time:
          return self.name + ' (' + ugettext('Requires starting time') + ')'

    return self.name

  class Meta:
    ordering = ('organisation', 'name')

class ExpenseTypeInline(admin.TabularInline):
  model = ExpenseType
  extra = 0
  can_delete = False
  fields = ('name', 'active', 'type', 'persontype', 'multiplier', 'requires_receipt', 'requires_endtime','requires_start_time', 'account', 'unit',)

class OrganisationAdmin(admin.ModelAdmin):
  ordering = ['name']
  inlines = [
    ExpenseTypeInline,
    AccountDimensionInline,
  ]

APPLICATION_STATUSES = (
  (0, ugettext_lazy('Open')),
  (1, ugettext_lazy('Sent')),
)

KATRE_STATUSES = (
  (0, ugettext_lazy('Open')),
  (1, ugettext_lazy('Not needed')),
  (2, ugettext_lazy('Sent')),
)

class Expense(models.Model):
  name = models.CharField(ugettext_lazy('Name'), max_length=255, validators=validators['name'])
  email = models.EmailField(ugettext_lazy('Email address'), validators=validators['email'])
  cc_email = models.EmailField(ugettext_lazy('CC email address'), blank=True, null=True, help_text=ugettext_lazy('Copy of the expense will be sent to the email.'), validators=validators['email'])
  phone = models.CharField(ugettext_lazy('Phone'), max_length=255, validators=validators['phoneno'])
  address = models.CharField(ugettext_lazy('Address'), max_length=255, validators=validators['address'])
  iban = IBANField(ugettext_lazy('Bank account no'))
  swift_bic = BICField(ugettext_lazy('BIC no'), blank=True, null=True)
  personno = models.CharField(ugettext_lazy('Person number'), max_length=11, validators=validators['hetu_or_businessid'], help_text=ugettext_lazy('If you apply for an expense reimbursement for a local group, enter the group’s business ID here. Kilometric allowances and daily subsistence allowances can not be applied for with a business ID.'))
  user = models.ForeignKey(User,on_delete=models.CASCADE)

  description = models.CharField(ugettext_lazy('Purpose'), max_length=255)
  memo = models.TextField(ugettext_lazy('Info'), help_text=ugettext_lazy('Names of the additional passengers, people in the meeting etc.'))
  organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
  status = models.IntegerField(ugettext_lazy('Status'), choices=APPLICATION_STATUSES, default=0)
  katre_status = models.IntegerField(ugettext_lazy('Katre status'), choices=KATRE_STATUSES, default=0)

  created_at = models.DateTimeField(ugettext_lazy('Sent'), auto_now_add=True)
  updated_at = models.DateTimeField(ugettext_lazy('Edited'), auto_now=True)

  def amount(self):
    sum = 0
    lines = ExpenseLine.objects.filter(expense=self)
    for line in lines:
      sum+= line.sum()
    return sum

  def __unicode__(self):
    return self.name + ': ' + self.description + ' (' + str(self.amount()) + ' e)'

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

# def receipt_path(path):
#   def wrapper(instance, filename):
#     import os
#     filename = filename.encode('ascii', 'ignore')
#     return os.path.join(path, filename)
#   return wrapper

def receipt_path(path, filename):
    import os
    filename = str(filename.encode('ascii', 'ignore'))
    return os.path.join(path, filename)

class ExpenseLine(models.Model):
  description = models.CharField(ugettext_lazy('Description'), max_length=255, help_text=ugettext_lazy('Description of the expense, eg. the route of the journey (travel expenses) or purpose of the purchased goods'))
  begin_at = models.DateTimeField(ugettext_lazy('Begin at'))
  ended_at = models.DateTimeField(ugettext_lazy('Ended at'), blank=True, null=True)

  expensetype = models.ForeignKey(ExpenseType, verbose_name=ugettext_lazy('Expense type'), on_delete=models.CASCADE)
  accountdimension = models.ForeignKey(AccountDimension, verbose_name=ugettext_lazy('Cost centre'), blank=True, null=True, on_delete=models.CASCADE)
  basis = models.DecimalField(ugettext_lazy('Amount'), max_digits=10, decimal_places=2, help_text=ugettext_lazy('Amount of kilometres, days or the sum of the expense'))
  expense = models.ForeignKey(Expense, on_delete=models.CASCADE)

  receipt = models.FileField(ugettext_lazy('Receipt'), upload_to='receipts', blank=True, null=True, help_text=ugettext_lazy('A scan or picture of the receipt. Accepted formats include PDF, PNG and JPG. Note: The receipt must clearly show what, when and how much has been paid!'))

  # These are in the ExpenseType too, but need to be duplicated to make sure that the data is retained after types are edited
  expensetype_name = models.CharField(ugettext_lazy('Name'), max_length=255)
  expensetype_type = models.CharField(ugettext_lazy('Type'), max_length=5, choices=EXPENSE_TYPES)
  multiplier = models.DecimalField(ugettext_lazy('Multiplier'), max_digits=10, decimal_places=2, help_text=ugettext_lazy('The per price for the expense type (mileage: € per km, other expenses: 1, advances: -1)'))
  
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
  fields = ('begin_at', 'ended_at', 'description', 'expensetype', 'basis', 'receipt',)

def open_katre_again(modeladmin, request, queryset):
    for expense in queryset:
        expense.katre_status = 0
        expense.save()
open_katre_again.short_description = 'Siirrä Katre-ilmoitus avoimeksi'

class ExpenseAdmin(admin.ModelAdmin):
  list_display = ('id', '__unicode__', 'organisation', 'status', 'katre_status', 'created_at')
  list_filter = (
    'status',
    'organisation',
    'katre_status',
    'user__person__type',
    ('created_at', DateFieldListFilter), # ?date__gte=2009-5-1&date__lt=2009-8-1
  )
  search_fields = ('name', 'email', 'description')
  inlines = [
    ExpenseLineInline,
  ]
  readonly_fields = ('created_at',)
  actions = [open_katre_again,]