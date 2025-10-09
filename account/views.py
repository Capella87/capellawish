from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import WishListUser
from account.serializers import UserSignUpSerializer


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
