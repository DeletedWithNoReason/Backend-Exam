from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from .models import Branch, Group, Subject, Lesson
from students.models import Student
from .serializers import (
    BranchSerializer, BranchDetailSerializer, 
    GroupSerializer, GroupCreateUpdateSerializer,
    SubjectSerializer, StudentSerializer, LessonSerializer, LessonCreateSerializer, LessonActionSerializer
)
from .permissions import IsAdmin, IsBranchAdmin, IsTeacher, IsBranchAdminOrReadOnly


@extend_schema(tags=['Branches'])
class BranchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBranchAdminOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['create_group', 'create_subject', 'recruit_student', 'create_lesson'] and 'pk' in self.kwargs:
            context['branch'] = self.get_object()
        return context

    def get_serializer_class(self):
        if not self.request or self.request.user.is_anonymous:
            return BranchSerializer

        if self.action == 'retrieve': return BranchDetailSerializer
        if self.action == 'create_group': return GroupCreateUpdateSerializer 
        if self.action == 'create_subject': return SubjectSerializer
        if self.action == 'recruit_student': return StudentSerializer
        if self.action == 'create_lesson': return LessonCreateSerializer
        if self.action in ['update', 'partial_update']:
            if isinstance(self.get_object(), Lesson):
                return LessonActionSerializer
            return BranchSerializer

        return BranchSerializer

    def get_queryset(self):
        
        if not self.request or self.request.user.is_anonymous:
            return Branch.objects.none()

        user = self.request.user
        if user.role == 'admin': return Branch.objects.all()
        if user.role == 'branch_admin':
            return Branch.objects.filter(branchmember__user=user).distinct()
        return Branch.active.for_user(user).distinct()

    def create(self, request, *args, **kwargs):
        if request.user.role == 'teacher':
            raise PermissionDenied("Teachers are not allowed to create branches.")
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=['Students'])
    @action(detail=True, methods=['get'], url_path='students')
    def list_students(self, request, pk=None):
        branch = self.get_object()
        students = Student.objects.filter(branch=branch)
        serializer = StudentSerializer(students, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(tags=['Groups'])
    @action(detail=True, methods=['get', 'post'], url_path='create-group')
    def create_group(self, request, pk=None):
        branch = self.get_object()
            
        if request.method == 'GET':
            return Response({'info': f'Creating group for branch {branch.name}'})
                
        serializer = GroupCreateUpdateSerializer(
            data=request.data, 
            context={'request': request, 'branch': branch, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save(branch=branch)

        fresh_group = Group.objects.annotate(
            annotated_student_count=Count('students')
        ).get(pk=group.pk)
        
        return Response(GroupSerializer(fresh_group, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['Subjects'])
    @action(detail=True, methods=['get', 'post'], url_path='create-subject')
    def create_subject(self, request, pk=None):
        branch = self.get_object()
        if request.method == 'GET':
            return Response({'info': f'Creating subject for branch {branch.name}'})
            
        serializer = SubjectSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(branch=branch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['Recruiting'])
    @action(detail=True, methods=['get', 'post'], url_path='recruit-student')
    def recruit_student(self, request, pk=None):
        branch = self.get_object()
        if request.method == 'GET':
            return Response({'info': f'Recruiting student for branch {branch.name}'})
            
        serializer = StudentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(branch=branch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        raise PermissionDenied("Teachers are not allowed to delete branches.")
    
    @extend_schema(tags=['Lessons'])
    @action(detail=True, methods=['get', 'post'], url_path='create-lesson')
    def create_lesson(self, request, pk=None):
        branch = self.get_object()
        
        if request.method == 'GET':
            return Response({'info': f'Creating lesson for branch {branch.name}'})
            
        serializer = LessonCreateSerializer(
            data=request.data, 
            context={'request': request, 'branch': branch, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Groups'])
class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBranchAdminOrReadOnly]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return GroupCreateUpdateSerializer
        return GroupSerializer

    def get_queryset(self):
        if not self.request or self.request.user.is_anonymous:
            return Group.objects.none()

        user = self.request.user
        if user.role == 'admin': 
            qs = Group.objects.all()
        elif user.role == 'branch_admin':
            qs = Group.objects.filter(branch__branchmember__user=user).distinct()
        else:
            qs = Group.active.for_user(user).distinct()
        
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        
        if self.action == 'list':
            return qs.annotate(annotated_student_count=Count('students'))
        return qs


@extend_schema(tags=['Subjects'])
class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsBranchAdminOrReadOnly]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        
        if not self.request or self.request.user.is_anonymous:
            return Subject.objects.none()

        user = self.request.user
        if user.role == 'admin': 
            qs = Subject.objects.all()
        elif user.role == 'branch_admin':
            qs = Subject.objects.filter(branch__branchmember__user=user).distinct()
        else:
            qs = Subject.active.for_user(user).distinct()

        
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
            
        return qs


@extend_schema(tags=['Lessons'])
class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin | IsBranchAdmin | IsTeacher]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return LessonActionSerializer
        return LessonSerializer

    def get_queryset(self):
        
        if not self.request or self.request.user.is_anonymous:
            return Lesson.objects.none()

        user = self.request.user
        if user.role == 'admin': 
            qs = Lesson.objects.all()
        elif user.role == 'branch_admin':
            qs = Lesson.objects.filter(group__branch__branchmember__user=user).distinct()
        elif user.role == 'teacher':
            qs = Lesson.objects.filter(teacher=user).exclude(status='archived')
        else:
            qs = Lesson.objects.filter(group__branch__branchmember__user=user).distinct()

        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(group__branch_id=branch_id)
            
        return qs
