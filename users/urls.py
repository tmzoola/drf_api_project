from django.urls import path
from .views import (CreateUserView,VerifyApiView,GetNewVerification,
                    ChangeUserInfoView,ChangeUserPhotoView,LoginView,LoginRefreshView,LogoutView)


urlpatterns = [
    path('login/',LoginView.as_view()),
    path('logout/',LogoutView.as_view()),
    path('login/refresh/',LoginRefreshView.as_view()),
    path('signup/',CreateUserView.as_view()),
    path('verify/',VerifyApiView.as_view()),
    path('resend_verify/',GetNewVerification.as_view()),
    path('change_user/',ChangeUserInfoView.as_view()),
    path('change_user_photo/',ChangeUserPhotoView.as_view()),
]