from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
import rest_framework.status
from capellawish.serializers import SampleSerializer


class MainView(APIView):
    """ This class is a main and sample view for the API."""

    permission_classes = [AllowAny]
    def get(self, request: Request) -> Response:
        """
        Returns a greeting message and a help message for POST requests.
        """
        messageresult = {
            "message": "Welcome to CapellaWish API",
            "help": "POST a title and description."
        }

        return Response(data=messageresult,
                        status=rest_framework.status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        data = SampleSerializer(data=request.data)

        if data.is_valid():
            return Response(data=data.data,
                            status=rest_framework.status.HTTP_200_OK)

        # Return error message with Problem Details format
        else:
            message = {
                "message": "Invalid data",
                "errors": data.errors
            }

            return Response(data=message,
                            status=rest_framework.status.HTTP_400_BAD_REQUEST)


class AuthenticatedMainView(APIView):
    permission_classes =  [IsAuthenticated]

    def get(self, request: Request) -> Response:
        data = {
            'message': f"Hello, {request.user}! You're authenticated."
        }

        return Response(data=data,
                        status=rest_framework.status.HTTP_200_OK)
