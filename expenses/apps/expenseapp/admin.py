# -*- coding: utf-8 -*-

from expenseapp.models import *
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class UserAdmin(UserAdmin):
  inlines = (PersonInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Person, PersonAdmin)