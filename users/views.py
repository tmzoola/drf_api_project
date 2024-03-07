from datetime import datetime

from rest_framework import generics
from rest_framework.generics import UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from shared.utils import send_email,check_email_or_phone
from .models import User,NEW,CODE_VERIFIED,VIA_PHONE,VIA_EMAIL
from .serializers import (SignUpSerializer, ChangeUserInfoSerializer, ChangeUserPhotoSerializer, LoginSerializer,
                          LoginRefreshSerializer, LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer)
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView



class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)



class VerifyApiView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify(user,code)

        data = {
            "status":True,
            "auth_status":user.auth_status,
            "access":user.token()['access'],
            "refresh":user.token()['refresh'],
            "message":"Code is verified"
        }

        return Response(data)

    @staticmethod
    def check_verify(user,code):
        verify_code = user.verify_codes.filter(expiration_time__gte=datetime.now(),code=code, is_confirmed=False)

        if not verify_code.exists():
            data = {
                "status":False,
                "message":"Confirmation code eskirgan yoki xato kiritilgan"
            }
            raise ValidationError(data)

        verify_code.update(is_confirmed=True)
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()

        return True

class GetNewVerification(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = self.request.user
        self.check_verification(user)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)

        else:
            data = {
                "status":False,
                "message":"Email yoki telefon raqam noto'g'ri kititildi"
            }

            raise ValidationError(data)

        data = {
            "status":True,
            "message":"Confirmation code qaytadan yuborildi"
        }

        return Response(data)

    @staticmethod
    def check_verification(user):
        verify_code = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)

        if verify_code.exists():
            data = {
                "status":False,
                "messaga":"Sizda tasdiqlash ko'di mavjud. Biroz kutib turing"
            }
            raise ValidationError(data)

class ChangeUserInfoView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeUserInfoSerializer
    http_method_names = ['put','patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInfoView,self).update(request, *args, **kwargs)

        data = {
            "status":True,
            "message":"User ma'lumotlari muvafaqiyatli o'zgartirildi",
            "auth_status":self.request.user.auth_status
        }
        return Response(data)
    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInfoView,self).update(request, *args, **kwargs)

        data = {
            "status":True,
            "message":"User ma'lumotlari muvafaqiyatli o'zgartirildi",
            "auth_status":self.request.user.auth_status
        }
        return Response(data)

class ChangeUserPhotoView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self,request, *args,**kwargs):
        serializer = ChangeUserPhotoSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)

            data = {
                "status":True,
                "message":"Rasm muvafaqiyatli o'zgartirildi"
            }
            return Response(data)

        return Response(serializer.errors)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer


    def post(self,request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                "status":True,
                "message":"You are logged out"
            }
            return Response(data)

        except TokenError:
            return Response(status=400)

class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = (AllowAny,)

    def post(self,request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        email_or_phone = serializer.validated_data.get('email_or_phone')
        user = serializer.validated_data.get('user')

        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(email_or_phone,code)

        elif check_email_or_phone(email_or_phone)=='email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone,code)

        data = {
            "status":True,
            "message":"Tasdiqlash kodi jo'natildi",
            "access":user.token()['access'],
            "refresh":user.token()['refresh']
        }

        return Response(data)


class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ResetPasswordView,self).update(request, *args,**kwargs)
        user = self.request.user

        data = {
            "status":True,
            "message":"Parolingiz muvafaqiyatli o'zgartirildi",
            "access":user.token()['access'],
            "refresh":user.token()['refresh']
        }

        return Response(data)