from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('list/', views.user_list, name='user_list'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('detail/<int:user_id>/', views.user_detail, name='user_detail'),
]