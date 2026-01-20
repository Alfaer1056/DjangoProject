# trips/models.py - ЗАМЕНИ весь файл на этот код

from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Встреча'),
        ('party', 'Вечеринка'),
        ('conference', 'Конференция'),
        ('training', 'Тренинг'),
        ('other', 'Другое'),
    ]

    LOCATION_TYPES = [
        ('address', 'Адрес'),
        ('online', 'Онлайн'),
        ('map', 'Точка на карте'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='meeting', verbose_name='Тип')

    # Дата и время
    start_datetime = models.DateTimeField(verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Дата и время окончания')

    # Место проведения
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPES, default='address', verbose_name='Тип места')
    address = models.CharField(max_length=500, blank=True, verbose_name='Адрес')
    online_link = models.URLField(blank=True, verbose_name='Онлайн-ссылка')
    latitude = models.FloatField(null=True, blank=True, verbose_name='Широта')
    longitude = models.FloatField(null=True, blank=True, verbose_name='Долгота')

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        ordering = ['-start_datetime']
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def get_location_display(self):
        if self.location_type == 'address':
            return self.address
        elif self.location_type == 'online':
            return f"Онлайн: {self.online_link}"
        elif self.location_type == 'map':
            return f"Точка на карте: {self.address}"
        return "Место не указано"


class EventParticipant(models.Model):
    """Участник мероприятия - ОБЪЕДИНЕННАЯ ВЕРСИЯ"""
    STATUS_CHOICES = [
        ('invited', 'Приглашен'),
        ('accepted', 'Принял'),
        ('declined', 'Отклонил'),
        ('confirmed', 'Подтвержден'),  # старое поле is_confirmed
    ]

    @property
    def status_display(self):
        """Отображаемое название статуса"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participating_events')
    invited_by = models.ForeignKey(User, related_name='invited_participants', null=True, blank=True,
                                   on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    role = models.CharField(max_length=50, blank=True, default='Участник')
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=True)  # Оставляем для обратной совместимости

    class Meta:
        unique_together = ['event', 'user']
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Синхронизируем статус с is_confirmed для обратной совместимости
        if self.status == 'accepted' or self.status == 'confirmed':
            self.is_confirmed = True
        else:
            self.is_confirmed = False
        super().save(*args, **kwargs)


class Expense(models.Model):
    """Расход на мероприятии"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200, verbose_name='На что потрачено')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid',
                                verbose_name='Кто оплатил')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_created')
    created_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False, verbose_name='Погашен')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Расход'
        verbose_name_plural = 'Расходы'

    def __str__(self):
        return f"{self.title} - {self.amount} руб."


class ExpenseParticipant(models.Model):
    """Кто должен за расход"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    share_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Доля')
    is_paid = models.BooleanField(default=False, verbose_name='Оплачено')

    class Meta:
        verbose_name = 'Участник расхода'
        verbose_name_plural = 'Участники расходов'

    def __str__(self):
        return f"{self.user.username} - {self.share_amount} руб."


class Task(models.Model):
    """Задача мероприятия"""
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
        ('cancelled', 'Отменено'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tasks', verbose_name='Назначена на')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-created_at']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friends_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'friend')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']


# В models.py добавьте:
class Notification(models.Model):
    """Уведомление для пользователя"""
    TYPE_CHOICES = [
        ('event_invitation', 'Приглашение в мероприятие'),
        ('friend_request', 'Заявка в друзья'),
        ('event_update', 'Изменение мероприятия'),
        ('expense_added', 'Новый расход'),
        ('task_assigned', 'Назначена задача'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='sent_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()