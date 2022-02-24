from django.urls import include, path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from expenseapp import views
from django.contrib.flatpages import views as flatviews
admin.site.site_header = 'Kululasku palvelun ylläpito'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('personinfo/', views.personinfo, name='personinfo'),
    path('i18n/<str:lang>', views.language_activate, name='language_activate'),
    path('organisation/<int:organisation_id>',
         views.organisationedit, name='organisation_edit'),
    path('organisation/<int:organisation_id>/annualreport/<str:year>',
         views.annualreport, name='organisation_annualreport'),
    path('expense/', views.organisationselection, name='expense_new'),
    path('expense/own/', views.ownexpenses, name='expense_own'),
    path('expense/<int:expense_id>', views.showexpense, name='expense_view'),
    path('expense/<int:expense_id>/xml',
         views.xmlexpense, name='expense_viewxml'),
    path('expense/<int:expense_id>/katre',
         views.katreexpense, name='expense_viewkatre'),
    path('expense/new/<int:organisation_id>',
         views.expense, name='expense_new_form'),
    path('receipt/<int:expenselineid>',
         views.receipt_fetch, name='receipt_fetch'),
    # Left from old version for a reminder.
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='django_registration/login.html'), name='auth_login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='django_registration/logout.html',
                                                           next_page='/accounts/login/'), name='logout'),
    path('accounts/change-password/', auth_views.PasswordChangeView.as_view(
        template_name='django_registration/password_change_form.html'), name='auth_password_change'),
    path('accounts/change-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='django_registration/password_change_done.html'), name='password_change_done'),
    path('accounts/password/reset/', auth_views.PasswordResetView.as_view(success_url='/accounts/password/reset/done/',
                                                                          template_name='django_registration/password_reset_form.html'), name="auth_password_reset"),
    path('accounts/password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='django_registration/password_reset_done.html'), name='auth_password_reset_done'),
    path('accounts/password/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='django_registration/password_reset_confirm.html'), name="password_reset_confirm"),
    path('accounts/password/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='django_registration/password_reset_complete.html'), name='password_reset_complete'),
    path('', flatviews.flatpage, {'url': '/index/'}, name='index'),
    path('', include('django.contrib.flatpages.urls'))
]
