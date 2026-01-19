# trips/views_api.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.utils import timezone
from .models import Event, Expense

from trips.forms import EventForm


# 1. Простой тестовый API
@login_required
def test_api(request):
    return JsonResponse({
        'status': 'success',
        'message': 'API работает!',
        'user': request.user.username
    })


# 2. API для создания мероприятия (упрощенная версия)
@login_required
@require_POST
@csrf_exempt
def create_event_api(request):
    """Создание мероприятия в БД"""
    try:
        data = json.loads(request.body)

        # Создаем форму с данными
        form = EventForm(data)

        if form.is_valid():
            # Сохраняем в БД
            event = form.save(commit=False)
            event.user = request.user  # ← ВАЖНО: привязываем к текущему пользователю!
            event.is_active = True  # ← Убедитесь, что мероприятие активно
            event.save()  # ← Сохраняем

            print(f"=== СОЗДАНО МЕРОПРИЯТИЕ ===")
            print(f"Пользователь: {request.user.username} (id={request.user.id})")
            print(f"Мероприятие: '{event.title}' (id={event.id})")

            return JsonResponse({
                'status': 'success',
                'message': 'Мероприятие создано в базе данных!',
                'event_id': event.id,
                'user': request.user.username
            })
        else:
            print(f"Ошибки формы: {form.errors}")
            return JsonResponse({
                'status': 'error',
                'message': 'Ошибки в форме',
                'errors': form.errors
            }, status=400)

    except Exception as e:
        print(f"Ошибка создания мероприятия: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка сервера: {str(e)}'
        }, status=500)


# 3. API для получения мероприятий (ОБНОВЛЕННАЯ ВЕРСИЯ)
@login_required
def get_my_events_api(request):
    """Получение РЕАЛЬНЫХ мероприятий пользователя из БД для календаря"""
    print(f"=== GET MY EVENTS API (календарь): user={request.user.username} ===")

    try:
        # Получаем реальные мероприятия из БД
        events = Event.objects.filter(user=request.user, is_active=True).order_by('-start_datetime')
        print(f"Найдено мероприятий в БД: {events.count()}")

        events_list = []
        for event in events:
            # Форматируем дату для календаря
            event_date = ''
            event_time = ''
            if event.start_datetime:
                event_date = event.start_datetime.strftime('%d.%m.%Y')
                event_time = event.start_datetime.strftime('%H:%M')

            # Получаем тип мероприятия
            event_type = event.get_event_type_display()

            # Определяем цвет по типу
            color_map = {
                'Встреча': '#0d6efd',
                'Вечеринка': '#dc3545',
                'Конференция': '#198754',
                'Тренинг': '#ffc107',
                'Поездка': '#6610f2',
                'Другое': '#6c757d'
            }
            event_color = color_map.get(event_type, '#6c757d')

            events_list.append({
                'id': event.id,
                'title': event.title,
                'description': event.description or '',
                'date': event_date,
                'time': event_time,
                'address': event.get_location_display() or '',
                'type': event_type,
                'color': event_color,
                'created_at': event.created_at.strftime('%d.%m.%Y %H:%M') if event.created_at else '',
                'creator': request.user.username,
                'allDay': False  # Для FullCalendar
            })
            print(f"  - ID:{event.id} '{event.title}' - {event_date} {event_time}")

        return JsonResponse({
            'status': 'success',
            'events': events_list,
            'total': len(events_list),
            'user': request.user.username,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        print(f"Ошибка получения мероприятий: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка загрузки мероприятий: {str(e)}'
        }, status=500)


# 4. API для удаления мероприятия
@login_required
@csrf_exempt
@require_POST
def delete_event_api(request, event_id):
    """Удаление мероприятия"""
    print(f"=== DELETE EVENT API CALLED: event_id={event_id} ===")

    return JsonResponse({
        'status': 'success',
        'message': f'Мероприятие {event_id} удалено (тест)'
    })


@login_required
def get_event_api(request, event_id):
    """API для получения одного мероприятия"""
    print(f"=== GET EVENT API CALLED: event_id={event_id} ===")

    # Тестовые данные
    test_events = {
        '1': {
            'title': 'Встреча с друзьями',
            'type': 'Встреча',
            'date': '15.12.2024',
            'time': '18:00',
            'address': 'Москва, Красная площадь',
            'description': 'Встреча с друзьями в центре города'
        },
        '2': {
            'title': 'Корпоратив',
            'type': 'Вечеринка',
            'date': '20.12.2024',
            'time': '19:00',
            'address': 'Санкт-Петербург, Невский пр.',
            'description': 'Корпоративное мероприятие'
        }
    }

    event_data = test_events.get(str(event_id), {
        'title': 'Мероприятие не найдено',
        'type': 'Неизвестно',
        'date': '--.--.----',
        'time': '--:--',
        'address': 'Не указано',
        'description': 'Мероприятие не найдено или удалено'
    })

    return JsonResponse({
        'status': 'success',
        'event': event_data
    })


@login_required
@csrf_exempt
def delete_event_view(request, event_id):
    """Удаление мероприятия (мягкое удаление)"""
    if request.method == 'POST':
        try:
            # Находим мероприятие текущего пользователя
            event = Event.objects.get(id=event_id, user=request.user)

            # Мягкое удаление - помечаем как неактивное
            event.is_active = False
            event.save()

            # ВСЕГДА возвращаем JSON для POST запросов
            return JsonResponse({
                'status': 'success',
                'message': 'Мероприятие удалено'
            })

        except Event.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Мероприятие не найдено'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка удаления: {str(e)}'
            }, status=500)

    # Если не POST запрос
    return JsonResponse({
        'status': 'error',
        'message': 'Недопустимый метод запроса'
    }, status=400)


# trips/views_api.py - добавь новую функцию
@login_required
def get_calendar_events_api(request):
    """API для календаря (FullCalendar формат)"""
    print(f"=== GET CALENDAR EVENTS API ===")

    try:
        events = Event.objects.filter(user=request.user, is_active=True)

        events_list = []
        for event in events:
            if event.start_datetime:
                # Для FullCalendar нужен формат ISO
                start_iso = event.start_datetime.isoformat()
                end_iso = None
                if event.end_datetime:
                    end_iso = event.end_datetime.isoformat()

                # Определяем цвет
                color_map = {
                    'meeting': '#0d6efd',
                    'party': '#dc3545',
                    'conference': '#198754',
                    'training': '#ffc107',
                    'trip': '#6610f2',
                    'other': '#6c757d'
                }
                event_color = color_map.get(event.event_type, '#6c757d')

                events_list.append({
                    'id': event.id,
                    'title': event.title,
                    'start': start_iso,
                    'end': end_iso,
                    'description': event.description or '',
                    'location': event.get_location_display() or '',
                    'type': event.get_event_type_display(),
                    'color': event_color,
                    'textColor': '#ffffff',
                    'url': f'/events/{event.id}/',  # Ссылка на страницу события
                    'extendedProps': {
                        'description': event.description or '',
                        'location': event.get_location_display() or '',
                        'type': event.get_event_type_display(),
                        'creator': request.user.username
                    }
                })

        return JsonResponse(events_list, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# API для системы денег и задач
@login_required
def get_event_expenses(request, event_id):
    """Получение расходов мероприятия"""
    try:
        event = Event.objects.get(id=event_id, user=request.user)
        expenses = Expense.objects.filter(event=event)

        expenses_data = []
        for expense in expenses:
            expenses_data.append({
                'id': expense.id,
                'title': expense.title,
                'amount': float(expense.amount),
                'paid_by': expense.paid_by.username,
                'paid_by_id': expense.paid_by.id,
                'created_at': expense.created_at.strftime('%d.%m.%Y'),
                'is_settled': expense.is_settled
            })

        return JsonResponse({
            'status': 'success',
            'expenses': expenses_data
        })

    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Мероприятие не найдено'}, status=404)


@login_required
@require_POST
@csrf_exempt
def add_expense(request, event_id):
    """Добавление расхода"""
    try:
        event = Event.objects.get(id=event_id, user=request.user)
        data = json.loads(request.body)

        # Создаем расход
        expense = Expense.objects.create(
            event=event,
            title=data['title'],
            amount=data['amount'],
            paid_by_id=data['paid_by_id'],
            created_by=request.user
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Расход добавлен',
            'expense_id': expense.id
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)