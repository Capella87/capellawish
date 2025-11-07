from typing import override
from urllib.parse import unquote

from allauth.account.models import EmailAddress
from allauth.account.views import ConfirmEmailView
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from allauth.account import app_settings as allauth_settings

from account.models import WishListUser
from account.serializers import UserSignUpSerializer, UserPasswordChangeSerializer, UserAccountSerializer, \
    EmailConfirmationSerializer, ResendEmailConfirmationSerializer


# Create your views here.

class UserAccountSignUpView(GenericAPIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]

    def create_response(self) -> Response:
        if allauth_settings.EMAIL_VERIFICATION == allauth_settings.EmailVerificationMethod.MANDATORY:
            return Response(data={
                'message': 'Confirmation email sent. Please check your inbox.'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'message': 'Successfully registered.'},
                            status=status.HTTP_201_CREATED)

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.create_response()


class UserAccountView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserAccountSerializer

    def get(self, request: Request) -> Response:
        user = request.user

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        user = request.user

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request) -> Response:
        user: WishListUser = request.user

        user.is_active = False
        user.save()

        return Response(data={'message': 'Account successfully deleted. Goodbye!'}, status=status.HTTP_200_OK)


class UserPasswordView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPasswordChangeSerializer

    def put(self, request: Request) -> Response:
        user = request.user
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.update(user, request.data)

        return Response(data={'message': 'Password successfully changed.'}, status=status.HTTP_200_OK)


# Source: https://github.com/iMerica/dj-rest-auth/blame/master/dj_rest_auth/registration/views.py
class EmailConfirmationView(APIView, ConfirmEmailView):
    permission_classes = [AllowAny]
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')
    serializer_class = EmailConfirmationSerializer

    @override
    def get(self, *args, **kwargs) -> Response:
        # TODO: Re-allow GET method to redirect to a frontend page...
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Note: unquote to handle URL-encoded keys
        self.kwargs['key'] = unquote(serializer.validated_data['key'])

        confirmation = self.get_object()
        result = confirmation.confirm(self.request)

        return Response(data={'message': 'Email is successfully verified.',
                              'email': result.email},
                        status=status.HTTP_200_OK)


class ResendEmailConfirmationView(GenericAPIView):
    serializer_class = ResendEmailConfirmationSerializer
    permission_classes = [AllowAny]
    queryset = EmailAddress.objects.all()

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_target = self.get_queryset().filter(**serializer.validated_data).first()
        if email_target and not email_target.verified:
            email_target.send_confirmation(request=request)

        return Response(data={'message': 'Confirmation email resent. Please check your inbox.'},
                        status=status.HTTP_200_OK)
