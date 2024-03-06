from datetime import datetime

from rest_framework import generics
from rest_framework.generics import UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from shared.utils import send_email
from .models import User,NEW,CODE_VERIFIED,DONE,PHOTO_STEP,VIA_PHONE,VIA_EMAIL
from .serializers import SignUpSerializer,ChangeUserInfoSerializer,ChangeUserPhotoSerializer,LoginSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView



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