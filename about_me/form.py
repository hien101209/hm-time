# forms.py
from django import forms
from .models import AboutMe

class AboutMeForm(forms.ModelForm):
    class Meta:
        model = AboutMe
        fields = ['name', 'short_description', 'profile_picture', 'email', 'linkedin', 'github', 'website']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 4}),
        }
