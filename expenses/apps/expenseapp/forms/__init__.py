import re
import json

from django import forms
from django.contrib import messages
from django.forms.models import inlineformset_factory
from crum import get_current_request
#from django_request_local.middleware import RequestLocal
from django.utils.translation import ugettext_lazy, ugettext as _
from django.db.models import Q

#from parsley.decorators import parsleyfy

from expenseapp.forms import inline_snippet
from expenseapp.models import Expense, ExpenseLine, ExpenseType, Person, Organisation, User

class ModelForm(inline_snippet.ModelForm):
  def __new__(cls, *args, **kwargs):
    new_class = super(ModelForm, cls).__new__(cls)
    #new_class = super(ModelForm, cls).__new__(*args)
    #new_class = super(ModelForm, cls).__new__(**kwargs)
    #new_class = super(ModelForm, cls).__new__(cls, *args, **kwargs)
    for field in list(new_class.base_fields.values()):
        if isinstance(field, forms.DecimalField):
          field.localize = True
          field.widget.is_localized = True
    return new_class

"""
Why do we need this? Well, young padawan, sit down and let me tell you a story.

* We're using parsley. It doesn't understand decimal comma in a DecimalField, so we
  need to use CharField and specify the validation regexp manually.
* Normally the Django l10n system converts DecimalFields from decimal comma to decimal
  point before submitting them to model. Naturally this doesn't happen with CharField,
  so we need to do it ourselves.
* The only brainful way to meddle with converting before any validation occurs and sinks
  the ship, we need to do it in to_python. Don't know if this is recommended, but it
  works and seems much better than any of the alternatives.

Keep this in mind when you think you have a better solution. Still, if you do, feel
free to fix it!
- Z / 7.11.2013
"""
class BasisField(forms.CharField):
  def to_python(self, value):
    value = value.replace(',', '.')
    return super(BasisField, self).to_python(value)

#@parsleyfy
class ExpenseLineForm(ModelForm):
  begin_at = forms.DateTimeField(label=ugettext_lazy('Begin at'),
    input_formats=('%d.%m.%Y %H.%M',))
  ended_at = forms.DateTimeField(label=ugettext_lazy('Ended at'),
    input_formats=('%d.%m.%Y %H.%M',),
    required=False)
  basis = BasisField(required=True,
    widget=forms.TextInput(attrs={'data-regexp':'^-?\d+([\,,\.](\d){1,2})?$', 'localization': True}),
    label=ugettext_lazy('Amount'),
    help_text=ugettext_lazy('Amount of kilometres, days or the sum of the expense'),
    localize=True)
  expensetype_data = forms.CharField(widget=forms.HiddenInput,
    required=False)

  class Meta:
    model = ExpenseLine
    exclude = ('expensetype_type', 'expensetype_name', 'multiplier', 'accountdimension',)

  def __init__(self, *args, **kwargs):
    #super(ExpenseLineForm, self).__init__(*args, **kwargs)
    super().__init__(*args, **kwargs)
    current_request = get_current_request()
    r = re.compile(r'^/expense/new/(?P<organisation_id>\d+)$')

    match = r.match(current_request.path)
    if match == None:
        messages.error(request, ugettext_lazy('Organisation ID was not found.'))
        return HttpResponseRedirect(reverse('expense_new'))

    orgid = int(match.groups()[0])
    organisation = Organisation.objects.get(id=orgid)
    expensetypes = ExpenseType.objects.filter(Q(persontype=current_request.user.person.type) | Q(persontype=None), organisation=organisation, active=True)

    self.fields["expensetype"].queryset = expensetypes
    self.fields["expensetype"].initial = str(organisation.default_expense_type.pk) if organisation.default_expense_type else None

    expensetypedata = []
    for expensetype in expensetypes:
      expensetypedata.append(expensetype.js_data())
    
    self.fields["expensetype_data"].initial = json.dumps(expensetypedata)

  def clean(self):
    #cleaned_data = super(ExpenseLineForm, self).clean()
    cleaned_data = super().clean()
    expensetype = cleaned_data.get("expensetype")
    ended_at = cleaned_data.get("ended_at")
    receipt = cleaned_data.get("receipt")

    if expensetype and expensetype.requires_endtime and not ended_at:
      self._errors["ended_at"] = self.error_class([ugettext_lazy('This expense type requires an ending time!')])

    if expensetype and expensetype.requires_receipt and not receipt:
      self._errors["receipt"] = self.error_class([ugettext_lazy('This expense type requires a receipt!')])

    return cleaned_data

ExpenseLineFormset = inlineformset_factory(Expense, ExpenseLine, form=ExpenseLineForm, extra=1, can_delete=False)

#@parsleyfy
class ExpenseForm(ModelForm):
  required_css_class = 'required'
  class Meta:
    model = Expense
    exclude = ('status', 'katre_status')
    widgets = {
      'organisation': forms.HiddenInput,
      'user': forms.HiddenInput,
   }

  class Forms:
    inlines = {
      'expenselines': ExpenseLineFormset,
    }


class PersonForm(ModelForm):
  firstname = forms.CharField(label=ugettext_lazy('First name'), max_length=255, required=True, widget=forms.TextInput())
  lastname = forms.CharField(label=ugettext_lazy('Last name'), max_length=255, required=True, widget=forms.TextInput())
  email = forms.EmailField(label=ugettext_lazy('Email'), max_length=255, required=True, widget=forms.EmailInput())

  def clean_email(self):
   email = self.cleaned_data['email']
   if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
       raise forms.ValidationError(ugettext_lazy("Email already exists"))
   return email


  class Meta:
    model = Person
    fields = ('firstname', 'lastname', 'email', 'personno', 'address', 'phone', 'iban', 'swift_bic', 'type', 'language')

    widgets = {
      'user': forms.HiddenInput,
    }


class ExpenseTypeForm(ModelForm):
  multiplier = forms.CharField(label=ugettext_lazy('Multiplier'))

  class Meta:
    model = ExpenseType
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    #super(ExpenseTypeForm, self).__init__(*args, **kwargs)
    super().__init__(*args, **kwargs)
    self.fields['account'].widget.attrs['class'] = "pure-input-1-3"
    self.fields['multiplier'].localize = False

ExpenseTypeFormset = inlineformset_factory(Organisation, ExpenseType, form=ExpenseTypeForm, extra=1, can_delete=False)

class OrganisationForm(ModelForm):
  class Meta:
    model = Organisation
    fields = '__all__'

  class Forms:
    inlines = {
      'expensetypes': ExpenseTypeFormset,
    }
