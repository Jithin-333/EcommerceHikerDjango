from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth import login

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return
        try:
            user = CustomUser.objects.get(email=user.email)
            sociallogin.connect(request, user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Your Google account has been connected to your existing account.')
            raise ImmediateHttpResponse(redirect('home'))
        except CustomUser.DoesNotExist:
            pass