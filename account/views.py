from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import WishListUser
from account.serializers import UserSignUpSerializer, UserPasswordChangeSerializer


# Create your views here.

class UserAccountSignUpView(APIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(data={'message': 'Successfully registered'},
                        status=status.HTTP_201_CREATED)


class UserAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request):
        user: WishListUser = request.user

        user.is_active = False
        user.save()

        return Response(data={'message': 'Account successfully deleted. Goodbye!'}, status=status.HTTP_200_OK)


class UserPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPasswordChangeSerializer

    def patch(self, request: Request) -> Response:
        user = request.user
        serializer = self.serializer_class(data=request.data, context=request)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.update(user, request.data)

        return Response(data={'message': 'Successfully changed password'}, status=status.HTTP_200_OK)
