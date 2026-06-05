from django import urls
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
    path('student/list/', views.student_list, name='student_list'),
    path('group/<int:pk>/students/', views.group_students, name='group_students'),
]