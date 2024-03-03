from django.shortcuts import render
from rest_framework import generics
from .models import User
from .serializers import SignUpSerializer
from rest_framework.permissions import AllowAny



class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)