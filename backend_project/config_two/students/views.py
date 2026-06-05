from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Student

@login_required
def student_list(request):
    if request.user.role == 'admin' or request.user.role == 'branch_admin':
        students = Student.objects.all()
    else:
        students = Student.objects.filter(status='active')
    return render(request, 'students/student_list.html', {'students': students})

@login_required
def student_detail(request, pk):
    from .models import Student
    student = Student.objects.get(pk=pk)
    parents = student.parents.all()
    return render(request, 'students/student_detail.html', {'student': student, 'parents': parents})

@login_required
def group_students(request, pk):
    from academics.models import Group
    group = Group.objects.get(pk=pk)
    if request.user.role == 'admin' or request.user.role == 'branch_admin':
        students = Student.objects.all()
    else:
        students = Student.objects.filter(status='active')
    subjects = group.subjects.all()
    return render(request, 'students/group_students.html', {'students': students, 'subjects': subjects})