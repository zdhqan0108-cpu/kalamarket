from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm,AddressForm,CustomAuthenticationForm
import jdatetime
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404,redirect
from .models import Address

def register(request):
    if request.user.is_authenticated:
        return redirect('account:profile')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # ====== لاگین خودکار ======
            login(request, user)
            
            messages.success(request, 'ثبت‌نام شما با موفقیت انجام شد.')
            return redirect('catalog:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'account/register.html', {'form': form})


@login_required
def profile(request):
    profile = request.user.profile
    jalali_date = jdatetime.datetime.fromgregorian(datetime=request.user.date_joined).strftime("%Y/%m/%d")
    
    if request.method == 'POST':
        
        request.user.username = request.POST.get('username')
        request.user.email = request.POST.get('email')
        request.user.save()
        
       
        profile.phone = request.POST.get('phone')
        profile.save()
        
        return redirect('account:profile')
    
    return render(request, 'account/profile.html', {
        'profile': profile,
        'jalali_date': jalali_date, 
    })

def to_jalali(date):
    """تبدیل تاریخ میلادی به شمسی"""
    return jdatetime.date.fromgregorian(date=date).strftime("%Y/%m/%d")

@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    user = request.user
        
    return render(request, 'account/address.html', {'addresses': addresses,'jalali_joined': to_jalali(user.date_joined),})


# اضافه کردن ادرس
@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
    return redirect('account:address')

# ویرایش ادرس
@login_required
def address_edit(request, pk):
    
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('account:address')  # برگشت به صفحه لیست آدرس‌ها
    else:
        form = AddressForm(instance=address)
    
    # گرفتن تمام آدرس‌های کاربر برای نمایش در قالب
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'account/address.html', {
    'addresses': Address.objects.filter(user=request.user),
    'editing_address': address,   # این خط رو اضافه کن
})

# حذف ادرس
@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    return JsonResponse({'status': 'ok'})



class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm  # ← استفاده از فرم جدید
    template_name = 'registration/login.html'




