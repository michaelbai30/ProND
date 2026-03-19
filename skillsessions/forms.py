from django import forms
from .models import Session


class SessionForm(forms.ModelForm): # form for creating/editing sessions - all fields except host, which is autoset in views
    class Meta:
        model = Session
        fields = ['skill', 'title', 'description', 'location', 'date_time', 'duration_minutes', 'capacity']
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '5'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        labels = {
            'duration_minutes': 'Duration (minutes)', # better label for duration field - decided to use minutes, happy to change
        }
