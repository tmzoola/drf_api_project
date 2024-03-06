import re
import threading

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError



phone_regex = re.compile(r"^\+998\d{2}\d{7}$")
email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
username_regex = re.compile(r'^[a-zA-Z0-9_]+$')

def check_email_or_phone(email_or_phone):

    if phone_regex.match(email_or_phone):
        email_or_phone='phone'
    elif email_regex.match(email_or_phone):
        email_or_phone ='email'
    else:
        data = {
            "status":False,
            "message":"email or phone is not valid"
        }
        raise ValidationError(data)

    return email_or_phone

def check_username_phone_email(email_or_phone_username):
    if phone_regex.match(email_or_phone_username):
        email_or_phone_username = 'phone'
    elif email_regex.match(email_or_phone_username):
        email_or_phone_username = 'email'
    elif username_regex.match(email_or_phone_username):
        email_or_phone_username = 'username'
    else:
        data = {
            "status": False,
            "message": "email or phone is not valid"
        }
        raise ValidationError(data)

    return email_or_phone_username




class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class Email:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data['content_type'] == 'html':
            email.content_subtype = 'html'

        EmailThread(email).start()

def send_email(email, code):
    html_content = render_to_string(
        'email/authentication/activate_account.html', {"code": code}
    )
    Email.send_email(
        {
            "subject": "Ro'yhatdan o'tish",
            "to_email": email,
            "body": html_content,
            "content_type": 'html'
        }
    )
