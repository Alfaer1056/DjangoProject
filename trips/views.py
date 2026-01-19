# views.py (в корне проекта)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from trips.forms import EventForm  # Импортируем форму из приложения trips


@login_required
def create_event_view(request):
    """Обработка создания мероприятия"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user  # Привязываем к текущему пользователю
            event.save()
            messages.success(request, 'Мероприятие успешно создано!')
            return redirect('my_events')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = EventForm()

    return render(request, 'create_event.html', {'form': form})


@login_required
def my_events_view(request):
    """Показ мероприятий пользователя"""
    from trips.models import Event  # Импортируем здесь, чтобы избежать циклического импорта
    events = Event.objects.filter(user=request.user, is_active=True).order_by('-start_datetime')
    print(f"=== MY EVENTS VIEW ===")
    print(f"Пользователь: {request.user.username}")
    print(f"Найдено мероприятий: {events.count()}")
    for e in events:
        print(f"  - {e.id}: {e.title}")
    return render(request, 'my_events.html', {'events': events})


@login_required
def event_detail_view(request, event_id):
    """Детальная страница мероприятия"""
    from trips.models import Event
    from django.shortcuts import get_object_or_404, render

    try:
        event = get_object_or_404(Event, id=event_id, user=request.user, is_active=True)

        # Подготавливаем данные для карты
        map_data = None
        if event.latitude and event.longitude:
            map_data = {
                'lat': float(event.latitude),
                'lng': float(event.longitude),
                'title': event.title,
                'address': event.address or 'Место проведения'
            }

        return render(request, 'event_detail.html', {
            'event': event,
            'map_data': map_data
        })

    except Event.DoesNotExist:
        # Если мероприятие не найдено или не активно
        return render(request, 'event_detail.html', {
            'error': 'Мероприятие не найдено или удалено',
            'event_id': event_id
        })


# Остальные views для TemplateView страниц
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class MainView(LoginRequiredMixin, TemplateView):
    template_name = 'main.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'


class MapView(LoginRequiredMixin, TemplateView):
    template_name = 'map.html'


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'calendar.html'


class FriendsView(LoginRequiredMixin, TemplateView):
    template_name = 'friends.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'


# trips/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Friendship, FriendRequest, Event, EventParticipant
from .forms import FriendSearchForm, FriendRequestForm, EventInviteForm
import json


@login_required
def friends_list_view(request):
    """Страница списка друзей"""
    # Получаем подтвержденных друзей
    friendships = Friendship.objects.filter(
        user=request.user,
        confirmed=True
    ).select_related('friend')

    # Получаем входящие заявки
    incoming_requests = FriendRequest.objects.filter(
        to_user=request.user,
        is_accepted=False
    ).select_related('from_user')

    # Получаем исходящие заявки
    outgoing_requests = FriendRequest.objects.filter(
        from_user=request.user,
        is_accepted=False
    ).select_related('to_user')

    # Форма поиска друзей
    search_form = FriendSearchForm()

    context = {
        'friends': [friendship.friend for friendship in friendships],
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'search_form': search_form,
        'active_tab': 'friends',
    }

    return render(request, 'friends.html', context)


@login_required
def search_friends_view(request):
    """Поиск пользователей для добавления в друзья"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Введите имя пользователя'}, status=400)
            else:
                messages.error(request, 'Введите имя пользователя для поиска')
                return redirect('friends')

        # Ищем пользователей (исключая себя)
        users = User.objects.filter(
            username__icontains=username
        ).exclude(id=request.user.id).order_by('username')[:10]

        # Получаем ID друзей
        friend_ids = Friendship.objects.filter(
            user=request.user,
            confirmed=True
        ).values_list('friend_id', flat=True)

        # Получаем отправленные заявки
        sent_requests = FriendRequest.objects.filter(
            from_user=request.user,
            is_accepted=False
        )
        sent_request_ids = sent_requests.values_list('to_user_id', flat=True)
        sent_request_dict = {req.to_user_id: req.id for req in sent_requests}

        # Получаем полученные заявки
        received_requests = FriendRequest.objects.filter(
            to_user=request.user,
            is_accepted=False
        )
        received_request_ids = received_requests.values_list('from_user_id', flat=True)
        received_request_dict = {req.from_user_id: req.id for req in received_requests}

        # Подготавливаем результаты
        results = []
        for user in users:
            is_friend = user.id in friend_ids
            has_sent_request = user.id in sent_request_ids
            has_received_request = user.id in received_request_ids

            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.strftime('%d.%m.%Y') if user.date_joined else '',
                'is_friend': is_friend,
                'has_sent_request': has_sent_request,
                'has_received_request': has_received_request,
            }

            # Добавляем ID заявок если есть
            if has_sent_request:
                user_data['sent_request_id'] = sent_request_dict.get(user.id)
            if has_received_request:
                user_data['received_request_id'] = received_request_dict.get(user.id)

            results.append(user_data)

        # Проверяем тип запроса
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX запрос - возвращаем JSON
            return JsonResponse({
                'success': True,
                'users': results,
                'count': len(results),
                'query': username
            })
        else:
            # Обычный POST запрос - возвращаем HTML
            return render(request, 'social/partials/search_results.html', {
                'users': results,
                'query': username
            })

    # GET запрос - перенаправляем на страницу друзей
    return redirect('friends')


import json
from django.http import JsonResponse


@login_required
def send_friend_request_view(request, user_id):
    """Отправка заявки в друзья (AJAX)"""
    print(f"=== ОТЛАДКА send_friend_request_view ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"To user ID: {user_id}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")

    if request.method == 'POST':
        try:
            to_user = get_object_or_404(User, id=user_id)

            # Проверяем, не друзья ли уже
            is_friend = Friendship.objects.filter(
                user=request.user,
                friend=to_user,
                confirmed=True
            ).exists()

            if is_friend:
                return JsonResponse({
                    'success': False,
                    'error': f'Вы уже друзья с {to_user.username}'
                })

            # Проверяем, не отправляли ли уже заявку
            existing_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=to_user,
                is_accepted=False
            ).first()

            if existing_request:
                return JsonResponse({
                    'success': False,
                    'error': f'Заявка уже отправлена {to_user.username}'
                })

            # Создаем заявку
            friend_request = FriendRequest.objects.create(
                from_user=request.user,
                to_user=to_user
            )

            return JsonResponse({
                'success': True,
                'message': f'Заявка отправлена {to_user.username}',
                'request_id': friend_request.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)

    print("Method not allowed")
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)


@login_required
def accept_friend_request_view(request, request_id):
    """Принятие заявки в друзья"""
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest,
            id=request_id,
            to_user=request.user
        )

        # Принимаем заявку
        friend_request.is_accepted = True
        friend_request.save()

        # Создаем двустороннюю дружбу
        Friendship.objects.get_or_create(
            user=request.user,
            friend=friend_request.from_user,
            confirmed=True
        )
        Friendship.objects.get_or_create(
            user=friend_request.from_user,
            friend=request.user,
            confirmed=True
        )

        messages.success(request, f'Вы теперь друзья с {friend_request.from_user.username}')

    return redirect('friends')


@login_required
def reject_friend_request_view(request, request_id):
    """Отклонение заявки в друзья"""
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest,
            id=request_id,
            to_user=request.user
        )
        friend_request.delete()
        messages.info(request, 'Заявка отклонена')

    return redirect('friends')


@login_required
def remove_friend_view(request, user_id):
    """Удаление из друзей"""
    if request.method == 'POST':
        friend = get_object_or_404(User, id=user_id)

        # Удаляем двустороннюю дружбу
        Friendship.objects.filter(
            user=request.user,
            friend=friend
        ).delete()
        Friendship.objects.filter(
            user=friend,
            friend=request.user
        ).delete()

        # Удаляем заявки
        FriendRequest.objects.filter(
            from_user=request.user,
            to_user=friend
        ).delete()
        FriendRequest.objects.filter(
            from_user=friend,
            to_user=request.user
        ).delete()

        messages.success(request, f'Пользователь {friend.username} удален из друзей')

    return redirect('friends')


@login_required
def invite_friend_to_event_view(request, event_id, user_id):
    """Приглашение друга в мероприятие"""
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        friend = get_object_or_404(User, id=user_id)

        # Проверяем, есть ли уже приглашение
        existing_invite = EventParticipant.objects.filter(
            event=event,
            user=friend
        ).first()

        if existing_invite:
            messages.info(request, f'{friend.username} уже приглашен')
        else:
            # Создаем приглашение
            EventParticipant.objects.create(
                event=event,
                user=friend,
                invited_by=request.user,
                status='invited'
            )

            messages.success(request, f'{friend.username} приглашен в мероприятие')

        return redirect('event_detail', event_id=event_id)

    return redirect('event_detail', event_id=event_id)


@login_required
def get_friends_ajax_view(request):
    """AJAX получение списка друзей"""
    friends = User.objects.filter(
        friendship__user=request.user,
        friendship__confirmed=True
    ).values('id', 'username', 'email')

    return JsonResponse({
        'success': True,
        'friends': list(friends)
    })