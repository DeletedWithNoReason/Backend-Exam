from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Branch, BranchMember

def is_authorized_for_branch(user, branch):
    if user.role == 'admin':
        return True
    return branch.staff_members.filter(id=user.id).exists()

def check_status(model_class, forbidden_statuses):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            obj_id = kwargs.get('pk') or kwargs.get('lesson_id') or kwargs.get('branch_id')
            obj = get_object_or_404(model_class, pk=obj_id)
            branch = obj if isinstance(obj, Branch) else getattr(obj, 'branch', None)
            if not branch and hasattr(obj, 'group'):
                branch = obj.group.branch
            elif not branch and hasattr(obj, 'lesson'):
                branch = obj.lesson.group.branch

            if request.user.role == 'admin':
                return view_func(request, *args, **kwargs)
            membership = None
            if branch:
                membership = branch.branchmember_set.filter(user=request.user).first()
                
            if not membership:
                raise PermissionDenied("403 Forbidden: You do not have access to this page.")
            if membership.role == 'manager':
                return view_func(request, *args, **kwargs)
            if hasattr(obj, 'status') and obj.status in forbidden_statuses:
                raise PermissionDenied("403 Forbidden: You do not have access to this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator