# trips/admin.py
from django.contrib import admin
from .models import Event  # ← Импортируем только существующую модель


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'event_type', 'start_datetime', 'location_type', 'is_active']
    list_filter = ['event_type', 'location_type', 'is_active', 'start_datetime']
    search_fields = ['title', 'description', 'address']
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'description', 'event_type')
        }),
        ('Дата и время', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Место проведения', {
            'fields': ('location_type', 'address', 'online_link', 'latitude', 'longitude')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )