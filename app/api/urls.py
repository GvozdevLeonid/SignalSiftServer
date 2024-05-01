from django.urls import path
from api import views

urlpatterns = [
    path('upload_file/', views.upload_file),
    path('add_file/', views.add_file),
]
