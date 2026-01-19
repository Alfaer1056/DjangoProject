from django.urls import path
from . import views
from .views import CustomRegistrationView
from .views import register_user

app_name = 'trips'

urlpatterns = [
     path('', views.home, name='home')
]