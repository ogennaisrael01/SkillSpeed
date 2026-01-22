from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


class CustomBackend(ModelBackend):
    def authenticate(self, request, username = ..., password = ..., **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if not any([username, password]):
            return 
        user = get_object_or_404(UserModel, email=username, is_active=True, account_status=UserModel.AccountStatus.ACTIVE)
        if UserModel.DoesNotExist:
            UserModel.set_password(password)
        else:
            if user.check_password(password):
                return user if self.user_can_authenticate(user) else None
    
    def get_user(self, user_id):
        UserMOdel = get_user_model()
        user = get_object_or_404(UserMOdel, pk=user_id, account_status=UserMOdel.AccountStatus.ACTIVE)
        if UserMOdel.DoesNotExist:
            return None
        else:
            return user if self.user_can_authenticate(user=user) else None
       