from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from account import views
from django.urls import path, include
from rest_framework import urls
from rest_framework import views

from account.views import UserAccountSignUpView, UserAccountView, UserPasswordView

app_name = 'account'
urlpatterns = [
    path('', UserAccountView.as_view(), name='user'),
    path('password/', UserPasswordView.as_view(), name='password_change'),
    path('signup/', UserAccountSignUpView.as_view(), name='SignUp'),
]
