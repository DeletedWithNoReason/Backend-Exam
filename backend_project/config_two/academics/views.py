from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from .models import Branch, Group, Lesson, Subject, Attendance
from .forms import AttendanceForm
from .decorators import check_status
from students.models import Student
from rest_framework import viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import LessonSerializer, CustomTokenObtainPairSerializer

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'admin':
        branches = Branch.objects.all() 
    else:
        branches = Branch.active.for_user(request.user)
    return render(request, 'academics/dashboard.html', {'branches': branches, 'user': user})

@login_required
@check_status(Branch, ['archived'])
def branch_detail(request, branch_id):
    branch = Branch.objects.get(id=branch_id)

    Lesson.objects.filter(
        group__branch=branch,
        status='scheduled',
        end_at__lt=timezone.now()
    ).update(status='completed')

    staff_members = branch.staff_members.all()
    user = request.user
    subjects = Subject.active.for_user(user).filter(branch=branch)
    groups = Group.active.for_user(user).filter(branch=branch)
    lessons = branch.schedule

    if user.role == 'teacher':
        lessons = lessons.filter(teacher=user)

    lesson_data = {
        'scheduled': lessons.filter(status='scheduled').order_by('start_at'),
        'completed': lessons.filter(status='completed').order_by('-start_at'),
        'canceled': lessons.filter(status='canceled').order_by('-start_at'),
    }

    return render(request, 'academics/branch_detail.html', {
        'branch': branch, 
        'subjects': subjects, 
        'groups': groups, 
        'staff_members': staff_members,
        **lesson_data,
        'user': user,
    })

@login_required
@check_status(Subject, ['archived'])
def subject_detail(request, branch_id, pk):
    subject = get_object_or_404(Subject, pk=pk, branch_id=branch_id)
    groups = Group.active.for_user(request.user).filter(subjects=subject)
    
    return render(request, 'academics/subject_detail.html', {
        'subject': subject, 
        'groups': groups,
        'branch_id': branch_id
    })

@login_required
@check_status(Group, ['archived'])
def group_detail(request, branch_id, pk):
    group = get_object_or_404(Group, pk=pk, branch_id=branch_id)
    user = request.user
    students = Student.active.for_user(user).filter(student_groups=group).order_by('first_name')
    subjects = Subject.active.for_user(user).filter(groups=group).order_by('name')
    
    return render(request, 'academics/group_detail.html', {
        'group': group, 
        'students': students, 
        'subjects': subjects,
        'branch_id': branch_id
    })

@login_required
@check_status(Lesson, ['archived'])
def lesson_detail(request, lesson_id, branch_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, group__branch_id=branch_id)
    branch = lesson.group.branch
    user = request.user

    if user.role == 'teacher' and lesson.teacher != user:
        raise PermissionDenied("You are not the teacher for this lesson.")
    
    students = Student.active.for_user(user).filter(student_groups=lesson.group).order_by('first_name')
    
    for student in students:
        Attendance.objects.get_or_create(lesson=lesson, student=student)

    AttendanceFormSet = modelformset_factory(Attendance, form=AttendanceForm, extra=0)

    if request.method == 'POST':

        if 'end_lesson' in request.POST:
            if lesson.status == 'scheduled':
                lesson.status = 'completed'
                lesson.save()
                messages.success(request, "Lesson has been successfully completed.")

            return redirect('academics:branch_detail', branch_id=branch_id)

        formset = AttendanceFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Attendance updated.")
            return redirect('academics:lesson_detail', branch_id=branch_id , lesson_id=lesson.id)
    else:
        formset = AttendanceFormSet(queryset=Attendance.objects.filter(lesson=lesson).order_by('student__first_name'))

    return render(request, 'academics/lesson_detail.html', {
        'lesson': lesson,
        'formset': formset,
        'branch': branch,
        'branch_id': branch_id,
    })

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer