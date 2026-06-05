from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'academics'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('branch/<int:branch_id>/', views.branch_detail, name='branch_detail'),
    path('branch/<int:branch_id>/subject/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('branch/<int:branch_id>/group/<int:pk>/', views.group_detail, name='group_detail'),
    path('branch/<int:branch_id>/group/<int:pk>/students/', views.group_detail, name='group_students'),
    path('branch/<int:branch_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('api/v1/auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


