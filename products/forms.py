from django import forms
from .models import CheckoutAddress,ReturnedProduct

class CheckoutAddressForm(forms.ModelForm):
    class Meta:
        model = CheckoutAddress
        fields = ['name','phone','phone_alternate', 'apartment_address', 'city', 'state', 'country', 'zip_code', 'address_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_alternate': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment_address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'address_type': forms.Select(attrs={'class': 'form-control'}),
        }



class ReturnProductForm(forms.ModelForm):
    class Meta:
        model = ReturnedProduct
        fields = ['reason', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }