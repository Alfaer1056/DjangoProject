from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from registration.backends.simple.views import RegistrationView
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.auth import views as auth_views

from trips import views
from trips.views import event_detail_view
from trips.views_api import delete_event_view, get_event_expenses, add_expense
from trips.views_api import get_calendar_events_api
urlpatterns = [
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/register/', RegistrationView.as_view(
        success_url='/',
        template_name='registration/registration_form.html'  # ЯВНО укажите шаблон
    ), name='register'),
    path('admin/', admin.site.urls),



    # allauth URLs - маршруты для аутентификации
    path('accounts/', include('allauth.urls')),

    # Маршруты для социального входа (опционально, можно ссылаться напрямую)
    path('social/login/vk/', TemplateView.as_view(template_name='social/vk_login.html'), name='vk_login'),
    path('social/login/google/', TemplateView.as_view(template_name='social/google_login.html'), name='google_login'),

    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('main/', TemplateView.as_view(template_name='main.html'), name='main'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('events/my/', TemplateView.as_view(template_name='my_events.html'), name='my_events'),
    path('events/create/', TemplateView.as_view(template_name='create_event.html'), name='create_event'),
    path('events/<int:event_id>/', event_detail_view, name='event_detail'),

path('events/<int:event_id>/delete/', delete_event_view, name='delete_event'),
path('api/events/calendar/', get_calendar_events_api, name='calendar_events_api'),
path('api/events/<int:event_id>/expenses/', get_event_expenses, name='event_expenses'),
path('api/events/<int:event_id>/expenses/add/', add_expense, name='add_expense'),

path('api/events/<int:event_id>/participants/', views.get_event_participants_api, name='event_participants_api'),

    path('calendar/', TemplateView.as_view(template_name='calendar.html'), name='calendar'),
    path('map/', TemplateView.as_view(template_name='map.html'), name='map'),
    path('settings/', TemplateView.as_view(template_name='settings.html'), name='settings'),
    path('trips/', include('trips.urls_api')),

    # Друзья
    path('friends/', views.friends_list_view, name='friends'),
    path('friends/search/', views.search_friends_view, name='search_friends'),
    path('friends/request/<int:user_id>/', views.send_friend_request_view, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request_view, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', views.reject_friend_request_view, name='reject_friend_request'),
    path('friends/remove/<int:user_id>/', views.remove_friend_view, name='remove_friend'),

path('events/<int:event_id>/invite/', views.invite_to_event_view, name='invite_to_event'),

    # Приглашения в мероприятия
    path('events/<int:event_id>/invite/<int:user_id>/', views.invite_friend_to_event_view,
         name='invite_friend_to_event'),
path('events/<int:event_id>/cancel-invite/<int:participant_id>/',
     views.cancel_event_invitation_view, name='cancel_event_invitation'),

path('friends/ajax/', views.get_friends_ajax, name='friends_ajax'),


# Профиль текущего пользователя
path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),

# Профиль другого пользователя (по ID)
path('profile/<int:user_id>/', TemplateView.as_view(template_name='profile.html'), name='user_profile'),

path('notifications/api/', views.get_notifications_api, name='notifications_api'),
path('events/invitation/<int:participant_id>/respond/', views.respond_to_invitation_view, name='respond_to_invitation'),

path('api/events/<int:event_id>/my-participant/', views.get_my_participant_api, name='my_participant_api'),

path('notifications/', views.notifications_view, name='notifications'),
path('notifications/api/', views.get_notifications_api, name='notifications_api'),

path('notifications/clear/', views.clear_notifications_api, name='clear_notifications'),
path('notifications/mark-all-read/', views.mark_all_read_api, name='mark_all_read'),


path('events/<int:event_id>/leave/', views.leave_event_view, name='leave_event'),
]