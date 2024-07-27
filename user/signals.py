# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver,Signal
from adminapp.models import CustomUser

# Define a custom signal
user_otp_verified = Signal()

@receiver(user_otp_verified)
def activate_user(sender, email, **kwargs):
    try:
        user = CustomUser.objects.get(email=email)
        user.is_active = True
        user.save()
    except CustomUser.DoesNotExist:
        pass