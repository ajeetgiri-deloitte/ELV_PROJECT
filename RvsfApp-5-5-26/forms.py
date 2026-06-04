from django import forms
from captcha.fields import CaptchaField, CaptchaTextInput
from .models import *

class LoginForm(forms.Form):
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))
    captcha = CaptchaField(
        widget=CaptchaTextInput(
            attrs={
                'class': 'form-control custom-captcha-input fst-italic',  # Add custom classes
                'placeholder': 'Enter Captcha',  # Add a placeholder
                'maxlength' : "6",
                'style': 'margin-top: 9px; ',  # Inline CSS styles
                
            }
        )
    )
    
class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'id': 'otp',
            'class': 'form-control',
            'placeholder': 'Enter OTP',
        })
    )
    captcha = CaptchaField(
        widget=CaptchaTextInput(attrs={
            'class': 'form-control custom-captcha-input fst-italic',
            'placeholder': 'Enter Captcha',
            'maxlength': '6',
            'style': 'margin-top: 9px;',
        })
    )
    
class CaptchaForm(forms.Form):
    captcha = CaptchaField(
        widget=CaptchaTextInput(
            attrs={
                'class': 'form-control custom-captcha-input fst-italic',  # Add custom classes
                'placeholder': 'Enter Captcha',  # Add a placeholder
                'maxlength' : "6",
                'style': 'margin-top: 9px; ',  # Inline CSS styles
                
            }
        )
    )