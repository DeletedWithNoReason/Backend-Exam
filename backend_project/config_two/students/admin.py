from django.contrib import admin
from .models import Student, Enrollment, Parent_GuardianData

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'branch', 'email', 'phone')
    list_filter = ('branch',)
    search_fields = ('first_name', 'last_name', 'email')
    filter_horizontal = ('parents',)

    def display_parent_guardian_data(self, obj):
        return ", ".join([f"{pgd.name} ({pgd.phone})" for pgd in obj.parents.all()])

@admin.register(Parent_GuardianData)
class Parent_GuardianDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'term')
    list_filter = ('term', 'subject')
