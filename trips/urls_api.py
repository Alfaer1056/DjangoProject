# trips/urls_api.py
from django.urls import path
from . import views_api

urlpatterns = [
    path('api/events/create/', views_api.create_event_api, name='create_event_api'),
    path('api/events/my/', views_api.get_my_events_api, name='get_my_events_api'),
    path('api/events/<int:event_id>/delete/', views_api.delete_event_api, name='delete_event_api'),
    path('trips/api/test/', views_api.test_api, name='test_api'),

]