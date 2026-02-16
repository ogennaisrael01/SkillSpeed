from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


class CustomBackend(ModelBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        user = UserModel.objects.get(email=username, is_active=True, 
                                     account_status=UserModel.AccountStatus.ACTIVE)
        if user.check_password(password):
            return user if self.user_can_authenticate(user) else None
        return None
    def get_user(self, user_id):
        UserMOdel = get_user_model()
        user = UserMOdel.objects.get(pk=user_id, account_status=UserMOdel.AccountStatus.ACTIVE)
        if UserMOdel.DoesNotExist:
            return None
        else:
            return user if self.user_can_authenticate(user=user) else None
       