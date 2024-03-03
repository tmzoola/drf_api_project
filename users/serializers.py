from rest_framework import serializers
from .models import UserConfirmation, User,VIA_PHONE,VIA_EMAIL,NEW,CODE_VERIFIED,DONE,PHOTO_STEP
from rest_framework.exceptions import ValidationError
from shared.utils import check_email_or_phone,send_email



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