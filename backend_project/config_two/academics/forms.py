from django import forms
from django.core.exceptions import ValidationError
from .models import Lesson, Attendance

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get("lesson_type")
        students = cleaned_data.get("students")

        if lesson_type == 'individual':
            if students and students.count() != 1:
                raise ValidationError("Individual lesson must have exactly one student.")
            if not students:
                raise ValidationError("Please select one student for the individual lesson.")
        
        return cleaned_data

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'mark', 'commentary']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'mark': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mark'}),
            'commentary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comment'}),
        }