from urllib import request
from django.contrib import admin

from students.models import Student
from .models import Branch, Group, Lesson, Subject, BranchMember
from .forms import LessonForm

class BranchMemberInline(admin.TabularInline):
    model = BranchMember
    extra = 1

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_staff', 'city', 'status') 
    search_fields = ('name', 'city')
    inlines = [BranchMemberInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('staff_members')

    def display_staff(self, obj):
        return ", ".join([f"{user.first_name} {user.last_name}" for user in obj.staff_members.all()])
    
    display_staff.short_description = 'Staff members'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'status')
    search_fields = ('name', 'branch__name')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch')
    search_fields = ('name', 'teacher__first_name', 'subject__name', 'teacher__last_name', 'branch__name')
    filter_horizontal = ('students', 'subjects')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.branch:
            form.base_fields['students'].queryset = Student.objects.filter(branch=obj.branch)
            form.base_fields['subjects'].queryset = Subject.objects.filter(branch=obj.branch)
        
        return form

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('name', 'lesson_type', 'group', 'start_at', 'end_at')
    search_fields = ('name', 'group__name', 'group__subject__name', 'group__teacher__first_name', 'group__teacher__last_name')
    filter_horizontal = ('students',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        instance = form.instance
        
        if instance.lesson_type == 'group_lesson':
            all_group_students = instance.group.students.all()
            instance.students.set(all_group_students)