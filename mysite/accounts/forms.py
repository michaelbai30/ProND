from django import forms
from .models import Profile, Skill


class ProfileForm(forms.ModelForm): # form for editing your profile - bio only (for now)
    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class SkillForm(forms.ModelForm): # form for editing your skills, put name + description
    class Meta:
        model = Skill
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
