from django.urls import path
from .views import PostListApiView, PostCreateView

urlpatterns = [
    path('list/', PostListApiView.as_view()),
    path('create/', PostCreateView.as_view()),
]
