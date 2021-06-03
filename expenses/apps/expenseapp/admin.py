# -*- coding: utf-8 -*-

from expenseapp.models import *
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class UserAdmin(UserAdmin):
  inlines = (PersonInline,)
  
def get_username_id(self):
    return '%s (%s)' % (self.username, str(self.id))

User.add_to_class("__str__", get_username_id)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Person, PersonAdmin)
