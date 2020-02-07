from django.urls import include, path, re_path
from django.contrib import admin
#from django.contrib.auth import urlpatterns
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from expenseapp import views
from django.contrib.flatpages import views as flatviews

import os

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()
#app_name = 'expenseapp'

urlpatterns =  [
  # Uncomment the next line to enable the admin:
  path('admin/', admin.site.urls),
  #path('', views.index, name='index'),
  path('personinfo/', views.personinfo, name='personinfo'),
  #TODO this bad boy :D
  path('i18n/', include('django.conf.urls.i18n')),

  #re_path(r'^i18n/(?P<lang>[a-z]+)$', views.language_activate, name='language_activate'),
  path('organisation/<int:organisation_id>/', views.organisationedit, name='organisation_edit'),
  path('organisation/<int:organisation_id>/annualreport/<str:year>', views.annualreport, name='organisation_annualreport'),
  path('expense/', views.organisationselection, name='expense_new'),
  path('expense/own/', views.ownexpenses, name='expense_own'),
  path('expense/<int:expense_id>', views.showexpense, name='expense_view'),
  path('expense/<int:expense_id>/xml', views.xmlexpense, name='expense_viewxml'),
  path('expense/<int:expense_id>/katre', views.katreexpense, name='expense_viewkatre'),
  path('expense/new/<int:organisation_id>', views.expense, name='expense_new_form'),
  path('receipt/<int:organisation_id>', views.receipt_fetch, name='receipt_fetch'),
  #TODO this bad boy :D
  #path(r'(?P<path>Finvoice.xsl)$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_ROOT, 'apps/expenseapp/static')}),
  #(r'(?P<path>Finvoice.css)$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_ROOT, 'apps/expenseapp/static')}),
  path('accounts/', include('django_registration.backends.activation.urls')),
  path('accounts/login/', auth_views.LoginView.as_view(template_name='django_registration/login.html'), name='auth_login'),
  path('accounts/logout/', auth_views.LogoutView.as_view(template_name='django_registration/logout.html', next_page='/accounts/login/'), name='logout'),
  path('accounts/change-password/', auth_views.PasswordChangeView.as_view(template_name='django_registration/password_change_form.html'), name='auth_password_change'),
  path('accounts/change-password/done/', auth_views.PasswordResetDoneView.as_view(template_name='django_registration/password_change_done.html'), name='auth_password_change_done'),
  path('accounts/password/reset/', auth_views.PasswordResetView.as_view(success_url='/accounts/password/reset/done/', template_name='django_registration/password_reset_form.html'), name="auth_password_reset"),
  path('accounts/password/reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='django_registration/password_reset_done.html'), name='auth_password_reset_done'),
  path('', flatviews.flatpage, {'url': '/index/'}, name='index'),
  path('', include('django.contrib.flatpages.urls')),
#   path(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
#       'django.contrib.auth.views.password_reset_confirm',
#       {'post_reset_redirect' : '/user/password/done/'},
#       name='password_reset_confirm'),

#   path(r'^user/password/done/$',
#       'django.contrib.auth.views.password_reset_complete'),
#   

  ]
    # Examples:
    # url(r'^$', 'expenses.views.home', name='home'),
    # url(r'^expenses/', include('expenses.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    
    

#     
#     
#             
#]

if settings.DEBUG:
    print((123))
  #urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns += patterns('',
#   url(r'^', include('django.contrib.flatpages.urls')),
# )
