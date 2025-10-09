from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from account import views
from django.urls import path, include
from rest_framework import urls

from account.views import UserAccountSignUpView, UserAccountView

app_name = 'account'
urlpatterns = [
    path('account/', UserAccountView.as_view(), name='user'),
    path('account/signup', UserAccountSignUpView.as_view(), name='SignUp'),
]
