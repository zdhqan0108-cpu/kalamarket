

from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'postal_code', 'address', 'description', 'payment_method', 'terms_accepted']
       