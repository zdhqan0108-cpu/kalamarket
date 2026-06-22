from django import forms
from .models import Address
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from .validators import validate_english_password


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='ایمیل')
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput,
        validators=[validate_english_password]
    )
    password2 = forms.CharField(
        label='تکرار رمز عبور',
        widget=forms.PasswordInput,
        validators=[validate_english_password]
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)

        # فارسی کردن خطاهای فیلدها
        self.fields['username'].error_messages['required'] = 'نام کاربری الزامی است.'
        self.fields['username'].error_messages['unique'] = 'این نام کاربری قبلاً ثبت شده است.'
        self.fields['username'].error_messages['invalid'] = 'نام کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و کاراکترهای @/./+/-/_ باشد.'
        
        self.fields['email'].error_messages['required'] = 'ایمیل الزامی است.'
        self.fields['email'].error_messages['invalid'] = 'ایمیل معتبر وارد کنید.'
        
        self.fields['password1'].error_messages['required'] = 'رمز عبور الزامی است.'
        self.fields['password1'].error_messages['invalid'] = 'رمز عبور فقط باید شامل حروف انگلیسی، اعداد و کاراکترهای مجاز باشد.'
        
        self.fields['password2'].error_messages['required'] = 'تکرار رمز عبور الزامی است.'
        self.fields['password2'].error_messages['password_mismatch'] = 'رمز عبور و تکرار آن مطابقت ندارند.'
        self.fields['password2'].error_messages['invalid'] = 'رمز عبور فقط باید شامل حروف انگلیسی، اعداد و کاراکترهای مجاز باشد.'
        
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('رمز عبور و تکرار آن مطابقت ندارند.')
        return password2

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].error_messages['required'] = 'نام کاربری الزامی است.'
        self.fields['password'].error_messages['required'] = 'رمز عبور الزامی است.'
        self.error_messages['invalid_login'] = 'نام کاربری یا رمز عبور اشتباه است.'


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['title', 'full_name', 'phone', 'address', 'city', 'postal_code']