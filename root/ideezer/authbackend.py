from .models import User


class Authbackend:
    def authenticate(self, request, deezer_id, deezer_name):
        try:
            user = User.objects.get(deezer_id=deezer_id)
            if deezer_name and user.username != deezer_name:
                user.username = deezer_name
                user.save()
        except User.DoesNotExist:
            user = User(deezer_id=deezer_id, username=deezer_name)
            user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
