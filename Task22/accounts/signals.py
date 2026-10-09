from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def set_admin_name(sender, user, request, **kwargs):
    if user.username.lower() == 'admin':
        if user.first_name != 'Swayam':
            user.first_name = 'Swayam'
            user.save(update_fields=['first_name'])
