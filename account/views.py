from dj_rest_auth.jwt_auth import set_jwt_cookies
from django.conf import settings
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import WishListUser
from account.serializers import UserSignUpSerializer, UserPasswordChangeSerializer, UserAccountSerializer


# Create your views here.

class UserAccountSignUpView(GenericAPIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Successfully registered.'},
                        status=status.HTTP_201_CREATED)


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
