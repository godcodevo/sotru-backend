import os
import requests
import boto3
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from backend.users.models import User

from .serializers import UserSerializer

def send_mail(email, content):
    email_params = {
        "apikey": os.getenv("MAIL_KEY"),
        "from": "ka.tahara.dev@gmail.com",
        "to": email,
        "subject": "Email Verify - Metricloop Account",
        "body": f"{content}",
        "isTransactional": True,
    }

    response = requests.post(
        "https://api.elasticemail.com/v2/email/send",
        data=email_params,
    )
    return response

class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
    
class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        try:
            data = request.data
            username = data["fullName"]
            email = data["email"]
            password = data["password"]
            confirmPassword = data["confirmPassword"]

            if password == confirmPassword:
                if len(password) >= 6:
                    if not User.objects.filter(email=email).exists():
                        user = User.objects.create_user(
                            email=email,
                            fullname=username,
                            password=password,
                        )
                        if User.objects.filter(email=email).exists():
                            # mail verify
                            refresh = RefreshToken.for_user(user)
                            response = send_mail(
                                email, f"{os.getenv('FRONT_URL')}/mail-verify/?token={str(refresh.access_token)}"
                            )
                            if response.status_code == 200:
                                return Response(
                                    {"success": "User created successfully and sent verification link."},
                                    status=status.HTTP_201_CREATED,
                                )
                            else:
                                return Response(
                                    {"success": "Resend verification link."},
                                    status=status.HTTP_201_CREATED,
                                )
                        else:
                            return Response(
                                {"error": "Something went wrong creating user"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
                    else:
                        return Response(
                            {"error": "Username already exists"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {"error": "Password must be at least 6 characters long"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            print(e)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
