# trips/forms.py
from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    end_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type',
            'start_datetime', 'end_datetime',
            'location_type', 'address', 'online_link',
            'latitude', 'longitude'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_type': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        location_type = cleaned_data.get('location_type')

        if end_datetime and end_datetime < start_datetime:
            raise forms.ValidationError('Дата окончания не может быть раньше даты начала')

        # Валидация места проведения
        if location_type == 'address' and not cleaned_data.get('address'):
            raise forms.ValidationError('Для типа "Адрес" укажите адрес')
        elif location_type == 'online' and not cleaned_data.get('online_link'):
            raise forms.ValidationError('Для типа "Онлайн" укажите ссылку')
        elif location_type == 'map' and (not cleaned_data.get('latitude') or not cleaned_data.get('longitude')):
            raise forms.ValidationError('Для типа "Точка на карте" выберите точку на карте')

        return cleaned_data

# trips/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import FriendRequest, EventParticipant

class FriendSearchForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )

class FriendRequestForm(forms.ModelForm):
    class Meta:
        model = FriendRequest
        fields = []

class EventInviteForm(forms.ModelForm):
    class Meta:
        model = EventParticipant
        fields = ['role']
        widgets = {
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Роль в поездке (опционально)'
            })
        }