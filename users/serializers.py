from typing import Dict, Any

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken

from .models import User,VIA_PHONE,VIA_EMAIL,NEW,CODE_VERIFIED,DONE,PHOTO_STEP
from rest_framework.exceptions import ValidationError,PermissionDenied
from shared.utils import check_email_or_phone,send_email,check_username_phone_email
from django.core.validators import FileExtensionValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer



class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(required=False, read_only=True)
    auth_status = serializers.CharField(required=False, read_only=True)


    def __init__(self, *args, **kwargs):
        super(SignUpSerializer,self).__init__(*args,**kwargs)
        self.fields['email_phone_number']=serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id','auth_type','auth_status')

    def create(self, validated_data):
        user = super(SignUpSerializer,self).create(validated_data)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)

        user.save()

        return user

    def validate(self,data):
        super(SignUpSerializer,self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data['email_phone_number']).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == 'email':
            data = {
                'email': user_input,
                'auth_type':VIA_EMAIL,
            }
        elif input_type == 'phone':
            data = {
                'phone_number': user_input,
                'auth_type':VIA_PHONE,
            }
        else:
            data = {
                "status":False,
                "message":"You must enter phone or email"
            }

            raise ValidationError(data)

        return data

    def validate_email_phone_number(self,value):
        value = value.lower()

        if value and User.objects.filter(email=value).exists():
            data = {
                "status":False,
                "message":"This email is already in our database"
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone_number=value).exists():
            data = {
                "status": False,
                "message": "This phone_number is already in our database"
            }
            raise ValidationError(data)

        return value


    def to_representation(self, instance):

        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())

        return data

class ChangeUserInfoSerializer(serializers.Serializer):
    first_name= serializers.CharField(write_only=True, required=True)
    last_name= serializers.CharField(write_only=True, required=True)
    username= serializers.CharField(write_only=True, required=True)
    password= serializers.CharField(write_only=True, required=True)
    confirm_password= serializers.CharField(write_only=True, required=True)


    def validate(self, data):
        password = data.get('password',None)
        confirm_password = data.get('confirm_password',None)

        if password !=confirm_password:
            data = {
                "status":False,
                "message":"Sizning parollar bir-biriga teng emas"
            }
            raise ValidationError(data)

        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data

    def validate_username(self,username):

        if len(username)<5 or len(username)>30:
            data={
                "status":False,
                "message":"Sizning username 5 va 30 char oralig'ida bo'lishi kerak"
            }
            raise ValidationError(data)

        if username.isdigit():
            data = {
                "status": False,
                "message": "Sizning username faqat sonlarda iborat bo'lmasligi kerak"
            }
            raise ValidationError(data)

        return username


    def update(self, instance, validated_data):
        instance.username = validated_data.get("username",instance.username)
        instance.first_name = validated_data.get("first_name",instance.first_name)
        instance.last_name = validated_data.get('last_name',instance.last_name)
        instance.password = validated_data.get('password', instance.password)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE

        instance.save()

        return instance

class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=[
        'jpg','jpeg','png','heic','heif'
    ])])


    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_STEP
            instance.save()

        return instance

class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer,self).__init__(*args,**kwargs)
        self.fields['userinput']=serializers.CharField(required=True)
        self.fields['username']=serializers.CharField(required=False, read_only=True)



    def auth_validate(self,data):
        user_input = data.get('userinput')

        if check_username_phone_email(user_input) == 'username':
            username = user_input

        elif check_username_phone_email(user_input) == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        elif check_username_phone_email(user_input) == 'email':
            user = self.get_user(email__iexact=user_input)
            username = user.username

        else:
            data = {
                "status":False,
                "message":"Username, Email, Phone xato kiritildi"
            }
            raise ValidationError(data)

        current_user = User.objects.filter(username__iexact=username).first()

        if current_user is not None and current_user.auth_status in [NEW,CODE_VERIFIED]:
            data = {
                "status":False,
                "message":"Siz ro'yhatdan to'liq o'tmagansiz"
            }
            raise ValidationError(data)

        user = authenticate(username=username, password=data['password'])

        if user is not None:
            self.user = user

        else:
            data={
                "status":False,
                "message": "Login yoki password xato kiritilgan"
            }
            raise ValidationError(data)


    def get_user(self,**kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            data = {
                "status":False,
                "message":"Bunday foydalanuchi mavjud emas"
            }
            raise ValidationError(data)


        return users.first()



    def validate(self,data):
        self.auth_validate(data)

        if self.user.auth_status not in [DONE,PHOTO_STEP]:
            raise PermissionDenied("siz login qila olmaysiz")


        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name']=self.user.full_name

        return data



class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, arrts: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(arrts)

        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None,user)

        return data



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True,required=True)

    def validate(self, data):
        email_or_phone = data.get('email_or_phone',None)

        if email_or_phone is None:
            data = {
                "status":False,
                "message":"Email yoki telefon raqam kiritilishi shart"
            }
            raise ValidationError(data)

        user = User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))

        if not user.exists():
            data = {
                "status": False,
                "message": "Email yoki telefon raqam topilmadi"
            }
            raise ValidationError(data)
        data['user'] = user.first()

        return data

class ResetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, required=True,write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True,write_only=True)

    class Meta:
        model = User
        fields = ('password', 'confirm_password')


    def validate(self, data):

        password = data.get('password',None)
        confirm_password = data.get('password',None)

        if password != confirm_password:
            data = {
                "status":False,
                "message":"Passwordlar bir-biriga teng emas"
            }
            raise ValidationError(data)

        if password:
            validate_password(password)

        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)

        return super(ResetPasswordSerializer,self).update(instance,validated_data)