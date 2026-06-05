from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kw):
        User = get_user_model()
        try:
            user = User.objects.get(phone=username)
        except User.DoesNotExist:
            return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None