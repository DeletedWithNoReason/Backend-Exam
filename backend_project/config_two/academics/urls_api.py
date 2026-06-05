from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from . import views_api

@api_view(['GET'])
def custom_api_root(request, format=None):
    return Response({
        "Navigation": {
            "Branches": reverse('branch-list', request=request, format=format)
        }
    })

router = SimpleRouter()

router.register(r'branches', views_api.BranchViewSet, basename='branch')
router.register(r'groups', views_api.GroupViewSet, basename='group')
router.register(r'subjects', views_api.SubjectViewSet, basename='subject')
router.register(r'lessons', views_api.LessonViewSet, basename='lesson')

urlpatterns = [
    path('', custom_api_root, name='custom-api-root'),
    path('', include(router.urls)),
]