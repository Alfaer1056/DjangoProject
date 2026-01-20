# views.py (в корне проекта)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from trips.forms import EventForm  # Импортируем форму из приложения trips
from django.db.models import Q

from . import models


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
    """Показ мероприятий пользователя - УПРОЩЕННАЯ И РАБОЧАЯ ВЕРСИЯ"""
    from trips.models import Event, EventParticipant

    print("=" * 60)
    print(f"MY EVENTS VIEW - Пользователь: {request.user.username} (ID: {request.user.id})")
    print("=" * 60)

    # 1. Мероприятия где пользователь организатор
    organized_events = Event.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-start_datetime')

    print(f"Организованные мероприятия: {organized_events.count()}")

    # 2. Мероприятия где пользователь участник - ПРОСТО И ПОНЯТНО!
    # Получаем ВСЕ записи EventParticipant для пользователя
    all_participations = EventParticipant.objects.filter(
        user=request.user
    ).select_related('event')

    print(f"\nВсе записи EventParticipant для пользователя: {all_participations.count()}")

    for p in all_participations:
        print(f"  - ID:{p.id}, Event ID:{p.event_id}, Status:'{p.status}', Event Title:'{p.event.title}'")

    # Фильтруем только подходящие статусы
    valid_statuses = ['accepted', 'confirmed', 'invited']  # Все кроме declined
    valid_participations = all_participations.filter(
        status__in=valid_statuses
    )

    print(f"\nЗаписи с валидными статусами {valid_statuses}: {valid_participations.count()}")

    # Получаем ID мероприятий
    event_ids = valid_participations.values_list('event_id', flat=True)
    print(f"ID мероприятий для участия: {list(event_ids)}")

    # Получаем сами мероприятия
    participating_events = Event.objects.filter(
        id__in=event_ids,
        is_active=True
    ).exclude(user=request.user)  # Исключаем где пользователь организатор

    print(f"Участвую в мероприятиях: {participating_events.count()}")
    for event in participating_events:
        print(f"  - ID:{event.id}, Title:'{event.title}', Организатор:{event.user.username}")

    # 3. Приглашения (только invited статус)
    pending_invitations = all_participations.filter(status='invited')
    print(f"\nОжидающие приглашения: {pending_invitations.count()}")

    # 4. ВСЕ мероприятия для отображения
    all_events = list(organized_events) + list(participating_events)

    print(f"\nИТОГО:")
    print(f"Организованные: {len(organized_events)}")
    print(f"Участвую: {len(participating_events)}")
    print(f"Приглашения: {pending_invitations.count()}")
    print(f"Всего мероприятий: {len(all_events)}")

    # ДЕБАГ: Если homa не видит мероприятия, проверим вручную
    if request.user.username == 'homa' and len(all_events) == 0:
        print("\n!!! ДЕБАГ ДЛЯ HOMA !!!")
        # Вручную проверим EventParticipant
        manual_check = EventParticipant.objects.filter(
            user__username='homa',
            status__in=['accepted', 'confirmed']
        )
        print(f"Ручная проверка EventParticipant для homa: {manual_check.count()}")
        for mp in manual_check:
            print(f"  - Event ID:{mp.event_id}, Status:{mp.status}")

            # Проверим существует ли мероприятие
            try:
                event = Event.objects.get(id=mp.event_id)
                print(f"    Мероприятие найдено: '{event.title}' (ID:{event.id}), is_active:{event.is_active}")
                if event.is_active:
                    print(f"    ДОБАВЛЯЕМ В СПИСОК!")
                    all_events.append(event)
                    participating_events = list(participating_events) + [event]
            except Event.DoesNotExist:
                print(f"    ОШИБКА: Мероприятие ID:{mp.event_id} не найдено!")

    print("=" * 60)

    return render(request, 'my_events.html', {
        'events': all_events,
        'organized_events': organized_events,
        'participating_events': participating_events,
        'pending_invitations': pending_invitations,
        'total_events': len(all_events),
        'debug': True
    })


@login_required
def event_detail_view(request, event_id):
    """Детальная страница мероприятия - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    from trips.models import Event, EventParticipant
    from django.shortcuts import get_object_or_404, render

    try:
        # Находим мероприятие (не проверяем user=request.user - участники тоже должны видеть)
        event = get_object_or_404(Event, id=event_id, is_active=True)

        # Проверяем доступ пользователя
        can_access = False

        # 1. Пользователь организатор
        if event.user == request.user:
            can_access = True

        # 2. Пользователь участник
        elif EventParticipant.objects.filter(event=event, user=request.user,
                                             status__in=['accepted', 'confirmed']).exists():
            can_access = True

        # 3. Пользователь приглашен (ожидает ответа)
        elif EventParticipant.objects.filter(event=event, user=request.user, status='invited').exists():
            can_access = True

        if not can_access:
            return render(request, 'event_detail.html', {
                'error': 'У вас нет доступа к этому мероприятию',
                'event_id': event_id
            })

        # Получаем участников мероприятия
        participants = EventParticipant.objects.filter(event=event).select_related('user', 'invited_by')

        # Определяем роль пользователя в мероприятии
        user_role = 'guest'
        user_participant = None

        if event.user == request.user:
            user_role = 'organizer'
        else:
            user_participant = EventParticipant.objects.filter(event=event, user=request.user).first()
            if user_participant:
                user_role = user_participant.status  # invited, accepted, etc.

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
            'participants': participants,
            'map_data': map_data,
            'user_role': user_role,
            'user_participant': user_participant,
            'can_edit': event.user == request.user,  # Только организатор может редактировать
        })

    except Event.DoesNotExist:
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
from .models import Friendship, FriendRequest, Event, EventParticipant, Notification
from .forms import FriendSearchForm, FriendRequestForm, EventInviteForm
import json


@login_required
def friends_list_view(request):
    """Страница списка друзей - ФИНАЛЬНАЯ ВЕРСИЯ"""
    from django.db.models import Q

    # 1. Находим всех друзей
    friendships = Friendship.objects.filter(
        confirmed=True
    ).filter(
        Q(user=request.user) | Q(friend=request.user)
    )

    # 2. Собираем ID всех друзей
    friend_ids = []
    for f in friendships:
        if f.user.id == request.user.id:
            friend_ids.append(f.friend.id)
        else:
            friend_ids.append(f.user.id)

    # 3. Получаем объекты User
    friends = User.objects.filter(id__in=friend_ids)

    # 4. Входящие заявки
    incoming_requests = FriendRequest.objects.filter(
        to_user=request.user,
        is_accepted=False
    ).select_related('from_user')

    # 5. Исходящие заявки
    outgoing_requests = FriendRequest.objects.filter(
        from_user=request.user,
        is_accepted=False
    ).select_related('to_user')

    # 6. Форма поиска
    search_form = FriendSearchForm()

    # 7. Контекст
    context = {
        'friends': friends,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'search_form': search_form,
        'active_tab': 'friends',
    }

    return render(request, 'friends.html', context)


@login_required
def search_friends_view(request):
    """Поиск пользователей для добавления в друзья - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
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

        # Получаем ID друзей (confirmed=True)
        friend_ids = Friendship.objects.filter(
            user=request.user,
            confirmed=True
        ).values_list('friend_id', flat=True)

        # ===== ИСПРАВЛЕННАЯ ЧАСТЬ =====
        # 1. Получаем ВСЕ заявки между пользователями
        all_requests = FriendRequest.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        )

        # Создаем словари для быстрого поиска
        sent_requests_dict = {}  # Я → другие
        received_requests_dict = {}  # Другие → я
        accepted_requests_dict = {}  # Принятые заявки

        for req in all_requests:
            if req.from_user == request.user:
                # Заявки, которые Я отправил
                sent_requests_dict[req.to_user.id] = {
                    'id': req.id,
                    'is_accepted': req.is_accepted
                }
                if req.is_accepted:
                    accepted_requests_dict[req.to_user.id] = req.id
            else:
                # Заявки, которые МНЕ отправили
                received_requests_dict[req.from_user.id] = {
                    'id': req.id,
                    'is_accepted': req.is_accepted
                }
                if req.is_accepted:
                    accepted_requests_dict[req.from_user.id] = req.id

        # 2. Восстанавливаем дружбу из принятых заявок
        for user in users:
            user_id = user.id

            # Проверяем, есть ли принятая заявка, но нет дружбы
            if user_id in accepted_requests_dict and user_id not in friend_ids:
                print(f"Восстанавливаем дружбу с {user.username} из принятой заявки")
                try:
                    # Создаем двустороннюю дружбу
                    Friendship.objects.get_or_create(
                        user=request.user,
                        friend=user,
                        defaults={'confirmed': True}
                    )
                    Friendship.objects.get_or_create(
                        user=user,
                        friend=request.user,
                        defaults={'confirmed': True}
                    )
                    # Добавляем в список друзей
                    friend_ids = list(friend_ids) + [user_id]
                except Exception as e:
                    print(f"Ошибка восстановления дружбы: {e}")

        # ===== ПОДГОТОВКА РЕЗУЛЬТАТОВ =====
        results = []
        for user in users:
            user_id = user.id

            # Основные статусы
            is_friend = user_id in friend_ids
            sent_info = sent_requests_dict.get(user_id)
            received_info = received_requests_dict.get(user_id)

            # Определяем тип заявки
            has_sent_request = sent_info is not None and not sent_info['is_accepted']
            has_received_request = received_info is not None and not received_info['is_accepted']
            has_accepted_request = (sent_info and sent_info['is_accepted']) or \
                                   (received_info and received_info['is_accepted'])

            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.strftime('%d.%m.%Y') if user.date_joined else '',
                'is_friend': is_friend,
                'has_sent_request': has_sent_request,
                'has_received_request': has_received_request,
                'has_accepted_request': has_accepted_request,  # НОВОЕ ПОЛЕ
            }

            # Добавляем ID заявок если есть
            if sent_info:
                user_data['sent_request_id'] = sent_info['id']
                user_data['sent_request_accepted'] = sent_info['is_accepted']
            if received_info:
                user_data['received_request_id'] = received_info['id']
                user_data['received_request_accepted'] = received_info['is_accepted']

            # Если есть принятая заявка, но мы не друзья (что-то пошло не так)
            if has_accepted_request and not is_friend:
                user_data['status'] = 'accepted_but_not_friends'
            elif is_friend:
                user_data['status'] = 'friends'
            elif has_sent_request:
                user_data['status'] = 'sent_pending'
            elif has_received_request:
                user_data['status'] = 'received_pending'
            else:
                user_data['status'] = 'no_relation'

            results.append(user_data)

        # Проверяем тип запроса
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX запрос - возвращаем JSON
            return JsonResponse({
                'success': True,
                'users': results,
                'count': len(results),
                'query': username,
                'debug': {
                    'total_users_found': users.count(),
                    'friend_ids': list(friend_ids),
                    'sent_requests': len(sent_requests_dict),
                    'received_requests': len(received_requests_dict),
                }
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
    """Отправка заявки в друзья (AJAX) - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    print(f"\n=== ОТЛАДКА send_friend_request_view ===")
    print(f"Пользователь: {request.user} (ID: {request.user.id})")
    print(f"Запрашиваемый пользователь ID: {user_id}")

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST запрос'}, status=405)

    try:
        # 1. Находим пользователя
        to_user = get_object_or_404(User, id=user_id)
        print(f"Найден пользователь: {to_user.username} (ID: {to_user.id})")

        # 2. Проверка: нельзя добавить самого себя
        if request.user.id == to_user.id:
            return JsonResponse({
                'success': False,
                'error': 'Нельзя добавить самого себя в друзья'
            })

        # 3. Проверка: уже друзья?
        is_already_friend = Friendship.objects.filter(
            user=request.user,
            friend=to_user,
            confirmed=True
        ).exists()

        print(f"Уже друзья? {is_already_friend}")

        if is_already_friend:
            return JsonResponse({
                'success': False,
                'error': f'Вы уже друзья с {to_user.username}'
            })

        # 4. Проверка ВСЕХ заявок в обе стороны
        # Используем Q-объекты для сложных запросов
        existing_requests = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user)
        )

        print(f"Всего заявок между пользователями: {existing_requests.count()}")

        # 4.1. Проверяем каждую заявку
        for req in existing_requests:
            status = "принята" if req.is_accepted else "отправлена"
            direction = "от вас" if req.from_user == request.user else "вам"
            print(f"  - Заявка {req.id}: {direction}, статус: {status}")

        # 4.2. Вы уже отправили заявку (любую - принятую или нет)
        your_request = existing_requests.filter(from_user=request.user).first()
        if your_request:
            if your_request.is_accepted:
                # Заявка уже принята - должны быть друзьями
                print(f"Заявка уже принята! Создаём записи дружбы...")
                Friendship.objects.get_or_create(
                    user=request.user,
                    friend=to_user,
                    defaults={'confirmed': True}
                )
                Friendship.objects.get_or_create(
                    user=to_user,
                    friend=request.user,
                    defaults={'confirmed': True}
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Вы теперь друзья с {to_user.username}!',
                    'already_friends': True
                })
            else:
                # Заявка ещё не принята
                print(f"Заявка уже отправлена (ID: {your_request.id})")
                return JsonResponse({
                    'success': False,
                    'error': f'Заявка уже отправлена {to_user.username}'
                })

        # 4.3. Вам отправили заявку (и она не принята)
        their_request = existing_requests.filter(from_user=to_user, is_accepted=False).first()
        if their_request:
            print(f"Вам уже отправили заявку (ID: {their_request.id})")
            return JsonResponse({
                'success': False,
                'error': f'{to_user.username} уже отправил вам заявку. Примите её!',
                'request_id': their_request.id
            })

        # 5. Всё проверено - создаём новую заявку
        print("Создание новой заявки...")
        friend_request = FriendRequest.objects.create(
            from_user=request.user,
            to_user=to_user
        )

        print(f"Заявка создана ID: {friend_request.id}")

        return JsonResponse({
            'success': True,
            'message': f'Заявка отправлена {to_user.username}',
            'request_id': friend_request.id
        })

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


@login_required
def accept_friend_request_view(request, request_id):
    """Принятие заявки в друзья - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    print(f"\n=== ACCEPT FRIEND REQUEST VIEW ===")
    print(f"Пользователь: {request.user.username} (ID: {request.user.id})")
    print(f"ID заявки для принятия: {request_id}")

    if request.method == 'POST':
        try:
            # Находим заявку
            friend_request = get_object_or_404(
                FriendRequest,
                id=request_id,
                to_user=request.user  # Заявка должна быть адресована текущему пользователю!
            )

            print(f"Найдена заявка:")
            print(f"  От: {friend_request.from_user.username} (ID: {friend_request.from_user.id})")
            print(f"  Кому: {friend_request.to_user.username} (ID: {friend_request.to_user.id})")
            print(f"  Текущий статус: {friend_request.is_accepted}")

            # Проверяем, не принята ли уже
            if friend_request.is_accepted:
                print("Заявка уже принята!")
                messages.info(request, 'Заявка уже была принята ранее')
            else:
                # Принимаем заявку
                friend_request.is_accepted = True
                friend_request.save()
                print("Заявка помечена как принятая")

                # Создаем двустороннюю дружбу
                friendship1, created1 = Friendship.objects.get_or_create(
                    user=request.user,
                    friend=friend_request.from_user,
                    defaults={'confirmed': True}
                )

                friendship2, created2 = Friendship.objects.get_or_create(
                    user=friend_request.from_user,
                    friend=request.user,
                    defaults={'confirmed': True}
                )

                print(f"Создана дружба 1: {created1} (ID: {friendship1.id})")
                print(f"Создана дружба 2: {created2} (ID: {friendship2.id})")

                messages.success(request, f'Вы теперь друзья с {friend_request.from_user.username}!')

        except Exception as e:
            print(f"ОШИБКА при принятии заявки: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Ошибка при принятии заявки: {str(e)}')

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
def get_friends_ajax(request):
    """AJAX получение списка друзей для приглашения"""
    # Получаем подтвержденных друзей
    friendships = Friendship.objects.filter(
        user=request.user,
        confirmed=True
    ).select_related('friend')

    friends_list = []
    for friendship in friendships:
        friends_list.append({
            'id': friendship.friend.id,
            'username': friendship.friend.username,
            'email': friendship.friend.email,
        })

    return JsonResponse({
        'success': True,
        'friends': friends_list,
        'count': len(friends_list)
    })


@login_required
def get_event_participants_api(request, event_id):
    """API для получения участников мероприятия"""
    try:
        event = Event.objects.get(id=event_id, user=request.user)
        participants = EventParticipant.objects.filter(event=event).select_related('user', 'invited_by')

        participants_list = []
        for participant in participants:
            participants_list.append({
                'id': participant.id,
                'user_id': participant.user.id,
                'username': participant.user.username,
                'role': participant.role,
                'status': participant.status,
                'status_display': participant.get_status_display(),
                'invited_by': participant.invited_by.username if participant.invited_by else 'Организатор',
                'created_at': participant.created_at.strftime('%d.%m.%Y %H:%M') if participant.created_at else ''
            })

        return JsonResponse({
            'success': True,
            'participants': participants_list,
            'count': len(participants_list),
            'event_title': event.title
        })

    except Event.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Мероприятие не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def invite_to_event_view(request, event_id):
    """AJAX: Приглашение друга в мероприятие"""
    try:
        event = Event.objects.get(id=event_id)
        data = json.loads(request.body)
        friend_id = data.get('friend_id')
        role = data.get('role', 'Участник')

        # Проверяем что это действительно друг
        is_friend = Friendship.objects.filter(
            user=request.user,
            friend_id=friend_id,
            confirmed=True
        ).exists()

        if not is_friend:
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не является вашим другом'
            })

        friend = User.objects.get(id=friend_id)

        # Проверяем не приглашен ли уже
        existing_invite = EventParticipant.objects.filter(
            event=event,
            user=friend
        ).first()

        if existing_invite:
            return JsonResponse({
                'success': False,
                'error': f'{friend.username} уже приглашен'
            })

        # Создаем приглашение
        participant = EventParticipant.objects.create(
            event=event,
            user=friend,
            invited_by=request.user,
            status='invited',
            role=role
        )

        # Создаем уведомление для друга
        Notification.objects.create(
            user=friend,
            notification_type='event_invitation',
            title=f'Приглашение в мероприятие',
            message=f'{request.user.username} пригласил вас в мероприятие "{event.title}"',
            related_event=event,
            related_user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'{friend.username} приглашен в мероприятие',
            'participant_id': participant.id,
            'participant': {
                'id': participant.id,
                'user_id': friend.id,
                'username': friend.username,
                'role': role,
                'status': 'invited',
                'status_display': 'Приглашен',
                'invited_by': request.user.username
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# В views.py добавьте:
@login_required
def get_notifications_api(request):
    """API для получения уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]

    notifications_list = []
    for notification in notifications:
        notifications_list.append({
            'id': notification.id,
            'type': notification.notification_type,
            'type_display': notification.get_notification_type_display(),
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
            'event_id': notification.related_event.id if notification.related_event else None,
            'event_title': notification.related_event.title if notification.related_event else None,
            'from_user': notification.related_user.username if notification.related_user else None,
            'from_user_id': notification.related_user.id if notification.related_user else None,
        })

    # Помечаем все как прочитанные
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return JsonResponse({
        'success': True,
        'notifications': notifications_list,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
    })


@login_required
@require_POST
def respond_to_invitation_view(request, participant_id):
    """Принять или отклонить приглашение в мероприятие - ИСПРАВЛЕННАЯ"""
    print(f"\n=== RESPOND TO INVITATION ===")
    print(f"Пользователь: {request.user.username}")
    print(f"Participant ID: {participant_id}")

    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'accept' или 'decline'

        print(f"Action: {action}")

        if action not in ['accept', 'decline']:
            return JsonResponse({
                'success': False,
                'error': 'Неверное действие. Используйте accept или decline'
            })

        # Находим приглашение
        participant = EventParticipant.objects.get(
            id=participant_id,
            user=request.user,  # Только приглашенный пользователь может отвечать
            status='invited'  # Только ожидающие ответа
        )

        event = participant.event
        print(f"Event found: {event.title}")
        print(f"Current status: {participant.status}")

        if action == 'accept':
            # Принимаем приглашение
            participant.status = 'accepted'
            participant.save()

            print(f"Status changed to: {participant.status}")

            # Создаем уведомление для организатора
            Notification.objects.create(
                user=participant.invited_by,
                notification_type='event_update',
                title='Приглашение принято',
                message=f'{request.user.username} принял ваше приглашение в мероприятие "{event.title}"',
                related_event=event,
                related_user=request.user
            )

            return JsonResponse({
                'success': True,
                'message': f'Вы приняли приглашение в мероприятие "{event.title}"',
                'participant': {
                    'id': participant.id,
                    'status': 'accepted',
                    'status_display': 'Принял',
                    'event_id': event.id,
                    'event_title': event.title
                }
            })

        else:  # decline
            # Отклоняем приглашение
            participant.status = 'declined'
            participant.save()

            print(f"Status changed to: {participant.status}")

            # Создаем уведомление для организатора
            Notification.objects.create(
                user=participant.invited_by,
                notification_type='event_update',
                title='Приглашение отклонено',
                message=f'{request.user.username} отклонил ваше приглашение в мероприятие "{event.title}"',
                related_event=event,
                related_user=request.user
            )

            return JsonResponse({
                'success': True,
                'message': f'Вы отклонили приглашение в мероприятие "{event.title}"',
                'participant': {
                    'id': participant.id,
                    'status': 'declined',
                    'status_display': 'Отклонил'
                }
            })

    except EventParticipant.DoesNotExist:
        print(f"Error: EventParticipant {participant_id} not found for user {request.user.username}")
        return JsonResponse({
            'success': False,
            'error': 'Приглашение не найдено или уже обработано'
        }, status=404)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



# Добавьте в views.py
@login_required
@require_POST
def cancel_event_invitation_view(request, event_id, participant_id):
    """Отмена приглашения в мероприятие"""
    try:
        # Находим приглашение
        participant = EventParticipant.objects.get(
            id=participant_id,
            event_id=event_id,
            invited_by=request.user,  # Только тот кто пригласил может отменить
            status='invited'  # Только ожидающие ответа
        )

        # Удаляем приглашение
        participant.delete()

        return JsonResponse({
            'success': True,
            'message': 'Приглашение отменено'
        })

    except EventParticipant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Приглашение не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def notifications_view(request):
    """Страница уведомлений пользователя"""
    return render(request, 'notifications.html')


@login_required
def get_my_participant_api(request, event_id):
    """Получить ID участника текущего пользователя для мероприятия"""
    try:
        event = Event.objects.get(id=event_id)
        participant = EventParticipant.objects.filter(event=event, user=request.user).first()

        if participant:
            return JsonResponse({
                'success': True,
                'participant_id': participant.id,
                'status': participant.status,
                'status_display': participant.get_status_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Вы не приглашены в это мероприятие',
                'participant_id': None
            })

    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)


@login_required
@require_POST
def clear_notifications_api(request):
    """Удалить все уведомления пользователя"""
    try:
        # Удаляем все уведомления пользователя
        count = Notification.objects.filter(user=request.user).count()
        Notification.objects.filter(user=request.user).delete()

        return JsonResponse({
            'success': True,
            'message': f'Удалено {count} уведомлений',
            'deleted_count': count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def mark_all_read_api(request):
    """Пометить все уведомления как прочитанные"""
    try:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

        return JsonResponse({
            'success': True,
            'message': f'{count} уведомлений помечены как прочитанные',
            'marked_count': count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# В views.py добавьте:
@login_required
@require_POST
def leave_event_view(request, event_id):
    """Выйти из мероприятия (для участников)"""
    try:
        event = Event.objects.get(id=event_id)
        participant = EventParticipant.objects.get(
            event=event,
            user=request.user,
            status__in=['accepted', 'confirmed']
        )

        # Изменяем статус на declined или удаляем
        participant.status = 'declined'
        participant.save()

        # Уведомление для организатора
        Notification.objects.create(
            user=event.user,
            notification_type='event_update',
            title='Участник покинул мероприятие',
            message=f'{request.user.username} покинул ваше мероприятие "{event.title}"',
            related_event=event,
            related_user=request.user
        )

        messages.success(request, f'Вы вышли из мероприятия "{event.title}"')

    except (Event.DoesNotExist, EventParticipant.DoesNotExist):
        messages.error(request, 'Ошибка: мероприятие не найдено')

    return redirect('my_events')