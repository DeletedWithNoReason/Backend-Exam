from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from academics.models import Branch
from .models import CustomUser

@login_required
def user_list(request):
    admins = CustomUser.objects.filter(role='admin')
    managers = CustomUser.objects.filter(role='branch_admin')
    teachers = CustomUser.objects.filter(role='teacher')
    
    return render(request, 'users/user_list.html', {
        'admins': admins,
        'managers': managers,
        'teachers': teachers
    })

@login_required
def user_detail(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    branch = Branch.objects.filter(staff_members=user).first()
    return render(request, 'users/user_detail.html', {'user': user, 'branch': branch})

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('username') 
        password = request.POST.get('password')
        
        if phone and password:
            user = authenticate(request, username=phone, password=password)
            
            if user:
                login(request, user)
                return redirect('academics:dashboard')
        
        return render(request, 'users/login.html', {
            'error': 'Invalid credentials or account is inactive.'
        })
        
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('users:login_view')