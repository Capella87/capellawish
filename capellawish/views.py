from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
import rest_framework.status
from capellawish.serializers import SampleSerializer


class MainView(GenericAPIView):
    """ This class is a main and sample view for the API."""

    permission_classes = [AllowAny]
    serializer_class = SampleSerializer
    def get(self, request: Request) -> Response:
        """
        Returns a greeting message and a help message for POST requests.
        """
        messageresult = {
            'message': 'Welcome to CapellaWish API',
            'help': 'POST a title and description.',
            'user_agent': request.META['HTTP_USER_AGENT'],
        }

        return Response(data=messageresult,
                        status=rest_framework.status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = SampleSerializer(data=request.data)

        if serializer.is_valid(raise_exception=False):
            data = serializer.data
            data.update({'user_agent': request.META['HTTP_USER_AGENT']})
            ret = Response(data=data,
                            status=rest_framework.status.HTTP_200_OK)
            ret.set_cookie(key='sample_cookie', value=f'{data["title"]}: {data["description"]}',
                           httponly=False, samesite='Lax', path='/', secure=False,
                           max_age=172_800) # 2 days
            return ret

        # Return error message with Problem Details format
        else:
            message = {
                'message': 'Invalid data',
                'errors': serializer.errors,
                'user_agent': request.META['HTTP_USER_AGENT'],
            }

            return Response(data=message,
                            status=rest_framework.status.HTTP_400_BAD_REQUEST)


class AuthenticatedMainView(GenericAPIView):
    permission_classes =  [IsAuthenticated]

    def get(self, request: Request) -> Response:
        data = {
            'message': f"Hello, {request.user}! You're authenticated.",
            'user_agent': request.META['HTTP_USER_AGENT'],
        }

        return Response(data=data,
                        status=rest_framework.status.HTTP_200_OK)
