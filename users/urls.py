from django.urls import path
from .views import CreateUserView,VerifyApiView,GetNewVerification


urlpatterns = [
    path('signup/',CreateUserView.as_view()),
    path('verify/',VerifyApiView.as_view()),
    path('resend_verify/',GetNewVerification.as_view())
]