from django.shortcuts import render, get_object_or_404,redirect
from .models import Category, Brand, Product,Subcategory,ProductType,Coupon,Wishlist,ProductNotification,Review,ProductVariant
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import json
import jdatetime
from .forms import ReviewForm
from django.db.models import Avg,Q
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

def add_remaining_stock(products, cart):
    for product in products:
        if product.variants.exists():
            total_stock = sum(v.stock for v in product.variants.all())
        else:
            total_stock = product.stock

        qty_in_cart = 0
        for key, item in cart.items():
            if '-' in key:
                pid = int(key.split('-')[0])
            else:
                pid = int(key)
            if pid == product.id:
                qty_in_cart += item.get('quantity', 0)

        product.remaining_stock = total_stock - qty_in_cart
    return products


def add_discount_to_products(products):
     for product in products:
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
     return products


def home(request):
    query = request.GET.get('q', '').strip()
    search_products = None
    search_message = None
    cart = request.session.get('cart', {})
    compare_list = request.session.get('compare_list', [])
    if query:
        # ====== ۱. چک کن با دسته‌بندی مطابقت داره (غیردقیق) ======
        category = Category.objects.filter(title__iexact=query).first()
        if category:
            return redirect('catalog:category_products', cat_slug=category.slug)

        subcategory = Subcategory.objects.filter(title__iexact=query).first()
        if subcategory:
            return redirect('catalog:subcategory_products', sub_slug=subcategory.slug)

        brand = Brand.objects.filter(title__iexact=query).first()
        if brand:
            return redirect('catalog:brand_products', brand_slug=brand.slug)

        product_type = ProductType.objects.filter(title__iexact=query).first()
        if product_type:
            return redirect('catalog:product_type', pt_slug=product_type.slug)

        # ====== ۲. جستجوی محصولات ======
        search_products = Product.objects.filter(
            Q(title__iexact=query) |
            Q(description__iexact=query) |
            Q(brand__title__iexact=query) |
            Q(category__title__iexact=query) |
            Q(subcategory__title__iexact=query)
        ).distinct()

        if search_products:
            search_message = f'{search_products.count()} محصول برای "{query}" یافت شد.'
        else:
            search_message = f'هیچ محصولی با عبارت "{query}" یافت نشد.'
            query = None  # ← فیلد جستجو خالی میشه

    # ====== محصولات ثابت ======
    amazing_products = add_discount_to_products(Product.objects.filter(is_amazing=True))
    moment_products = add_discount_to_products(Product.objects.filter(is_moment=True)[:5])
    mobile_products = add_discount_to_products(Product.objects.filter(subcategory__slug='موبایل')[:5])
    camera_products = add_discount_to_products(Product.objects.filter(product_type__slug='دوربین-عکاسی')[:5])
    home_appliance_products = add_discount_to_products(Product.objects.filter(category__slug='خانه-و-اشپزخانه')[:5])

    # ====== اضافه کردن remaining_stock فقط به این سه بخش ======
    for product in mobile_products:
        total_stock = sum(v.stock for v in product.variants.all()) if product.variants.exists() else product.stock
        qty_in_cart = 0
        for key, item in cart.items():
            if '-' in key:
                pid = int(key.split('-')[0])
            else:
                pid = int(key)
            if pid == product.id:
                qty_in_cart += item.get('quantity', 0)
        product.remaining_stock = total_stock - qty_in_cart


    for product in camera_products:
        total_stock = sum(v.stock for v in product.variants.all()) if product.variants.exists() else product.stock
        qty_in_cart = 0
        for key, item in cart.items():
            if '-' in key:
                pid = int(key.split('-')[0])
            else:
                pid = int(key)
            if pid == product.id:
                qty_in_cart += item.get('quantity', 0)
        product.remaining_stock = total_stock - qty_in_cart


    for product in home_appliance_products:
        total_stock = sum(v.stock for v in product.variants.all()) if product.variants.exists() else product.stock
        qty_in_cart = 0
        for key, item in cart.items():
            if '-' in key:
                pid = int(key.split('-')[0])
            else:
                pid = int(key)
            if pid == product.id:
                qty_in_cart += item.get('quantity', 0)
        product.remaining_stock = total_stock - qty_in_cart

    # ====== تایم‌استمپ برای amazing_products ======
    for product in amazing_products:
        discount = product.discounts.filter(end_time__gte=timezone.now()).first()
        product.discount_timestamp = int(discount.end_time.timestamp()) * 1000 if discount else None

    # ====== علاقه‌مندی‌ها ======
    liked_products = []
    if request.user.is_authenticated:
        liked_products = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'catalog/home.html', {
        'amazing_products': amazing_products,
        'moment_products': moment_products,
        'mobile_products': mobile_products,
        'camera_products': camera_products,
        'home_appliance_products': home_appliance_products,
        'liked_products': liked_products,
        'query': query,
        'search_products': search_products,
        'search_message': search_message,
        'compare_list': compare_list,
    })


def category_products(request, cat_slug):
    category = get_object_or_404(Category, slug=cat_slug)
    products_list = Product.objects.filter(category=category)
    compare_list = request.session.get('compare_list', [])
     # ====== دریافت سبد خرید ======
    cart = request.session.get('cart', {})
    
    # ====== اضافه کردن remaining_stock ======
    products_list = add_remaining_stock(products_list, cart)
    # ====== اعمال تخفیف به محصولات ======
    for product in products_list:
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
    
    # ====== صفحه‌بندی ======
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    liked_products = set()
    if request.user.is_authenticated:
        liked_products = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'category': category,
        'liked_products': liked_products,
        'title': f'محصولات دسته {category.title}',
        'compare_list': compare_list,
    })



def subcategory_products(request, sub_slug):
    sub = get_object_or_404(Subcategory, slug=sub_slug)
    products_list = Product.objects.filter(subcategory=sub)
    cart = request.session.get('cart', {})
    compare_list = request.session.get('compare_list', [])
    
    # ====== اضافه کردن remaining_stock ======
    products_list = add_remaining_stock(products_list, cart)
    # ====== اعمال تخفیف به محصولات این زیردسته ======
    for product in products_list:
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
    
    # ====== صفحه‌بندی ======
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    liked_products = set()
    if request.user.is_authenticated:
        liked_products = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'liked_products': liked_products,
        'title': f'محصولات {sub.title}',
        'compare_list': compare_list,
    })


def brand_products(request, brand_slug):
    brand = get_object_or_404(Brand, slug=brand_slug)
    products_list = Product.objects.filter(brand=brand)
    cart = request.session.get('cart', {})
    compare_list = request.session.get('compare_list', [])
    
    # ====== اضافه کردن remaining_stock ======
    products_list = add_remaining_stock(products_list, cart)
    # ====== اعمال تخفیف به محصولات این برند ======
    for product in products_list:
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
    
    # ====== صفحه‌بندی ======
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    liked_products = set()
    if request.user.is_authenticated:
        liked_products = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'liked_products': liked_products,
        'title': f'محصولات برند {brand.title}',
        'compare_list': compare_list, 
    })

def product_type_products(request, pt_slug):
    pt = get_object_or_404(ProductType, slug=pt_slug)
    products_list = Product.objects.filter(product_type=pt)
    cart = request.session.get('cart', {})
    compare_list = request.session.get('compare_list', [])
    
    # ====== اضافه کردن remaining_stock ======
    products_list = add_remaining_stock(products_list, cart)
    # ====== اعمال تخفیف به محصولات این نوع ======
    for product in products_list:
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
    
    # ====== صفحه‌بندی ======
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    liked_products = set()
    if request.user.is_authenticated:
        liked_products = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'liked_products': liked_products,
        'title': f'محصولات {pt.title}',
         'compare_list': compare_list,
    })


def product_list(request):
    products_list = Product.objects.all()
    compare_list = [int(i) for i in request.session.get('compare_list', []) if str(i).isdigit()]    # ====== دریافت سبد خرید ======
    cart = request.session.get('cart', {})
    
    # ====== اعمال تخفیف و محاسبه remaining_stock ======
    for product in products_list:
        # ====== تخفیف ======
        discount = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        if discount:
            product.discount_percent = discount.discount_percent
            product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        else:
            product.discount_percent = None
            product.discounted_price = None
        
        # ====== محاسبه موجودی کل ======
        if product.variants.exists():
            total_stock = sum(variant.stock for variant in product.variants.all())
        else:
            total_stock = product.stock
        
        # ====== تعداد موجود در سبد خرید ======
        qty_in_cart = 0
        for key, item in cart.items():
            if '-' in key:
                product_id = int(key.split('-')[0])
            else:
                product_id = int(key)
            if product_id == product.id:
                qty_in_cart += item.get('quantity', 0)
        
        # ====== موجودی باقی‌مانده ======
        product.remaining_stock = total_stock - qty_in_cart
    
    # ====== صفحه‌بندی ======
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # ====== علاقه‌مندی‌ها ======
    liked_products = []
    if request.user.is_authenticated:
        liked_products = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'liked_products': liked_products,
         'compare_list': compare_list, 
    })

def add_to_cart(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    quantity = int(request.GET.get('quantity', 1))
    variant_id = request.GET.get('color')  # همون رنگ

    variant = None
    if variant_id:
        variant = product.variants.filter(id=variant_id).first()

    stock = variant.stock if variant else product.stock

    # 🔥 کلید مهم: product + variant
    key = f"{product_id}-{variant_id}" if variant_id else str(product_id)

    current_qty = cart.get(key, {}).get('quantity', 0)

    new_qty = current_qty + quantity

    if new_qty > stock:
        request.session['product_msg'] = f'تعداد بیشتر از موجودی ({stock}) است.'
        request.session['msg_type'] = 'danger'

    else:
        cart[key] = {
            "product_id": product_id,
            "variant_id": variant.id if variant else None,
            "quantity": new_qty,
            "name": product.title,
            "variant_name": variant.color if variant else None,
        }

        request.session['cart'] = cart

        request.session['product_msg'] = f'{quantity} عدد اضافه شد'
        request.session['msg_type'] = 'success'

    return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    # پیدا کردن کلید مناسب
    for key in list(cart.keys()):
        if key.startswith(str(product_id)):
            cart.pop(key, None)
            break

    request.session['cart'] = cart
    return redirect('catalog:cart_detail')
    




def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        # پیدا کردن کلید مناسب (چون ممکنه ترکیبی باشه)
        key = None
        for k in cart:
            if k.startswith(str(product_id)):
                key = k
                break

        if not key:
            return redirect('catalog:cart_detail')

        # دریافت مقدار جدید
        if 'decrement' in request.POST:
            new_qty = cart[key]['quantity'] - 1
        elif 'increment' in request.POST:
            new_qty = cart[key]['quantity'] + 1
        else:
            new_qty = int(request.POST.get('quantity', 1))

        # حذف یا بروزرسانی
        if new_qty <= 0:
            cart.pop(key, None)
        else:
            cart[key]['quantity'] = new_qty

        request.session['cart'] = cart

    return redirect('catalog:cart_detail')

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']

    return redirect('catalog:cart_detail')




def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []

    subtotal = 0
    total_product_discount = 0

    for product_id, item in cart.items():

        product = Product.objects.get(id=item['product_id'])
        quantity = item.get('quantity', 1)
        variant_id = item.get('variant_id')

        variant = None
        if variant_id:
            variant = ProductVariant.objects.filter(id=variant_id).first()

        price = int(product.price)

        # discount
        discount_obj = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        if discount_obj:
            discount_percent = discount_obj.discount_percent
            discounted_price = price - (price * discount_percent // 100)
        else:
            discount_percent = None
            discounted_price = price

        cart_items.append({
            'id': product.id,
            'name': product.title,
            'image': product.image,
            'slug': product.slug,
            'stock': variant.stock if variant else product.stock,
            'price': price,
            'discounted_price': discounted_price,
            'discount_percent': discount_percent,
            'quantity': quantity,
            'item_total': discounted_price * quantity,
            'color_name': variant.color if variant else None,
        })

        subtotal += price * quantity
        total_product_discount += (price - discounted_price) * quantity

    after_product_discount = subtotal - total_product_discount

    coupon_percent = request.session.get('coupon_percent', 0)
    coupon_discount = after_product_discount * coupon_percent // 100 if coupon_percent else 0

    after_coupon = after_product_discount - coupon_discount
    tax = after_coupon * 9 // 100
    grand_total = after_coupon + tax

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total_product_discount': total_product_discount,
        'after_product_discount': after_product_discount,
        'coupon_discount': coupon_discount,
        'coupon_percent': coupon_percent,
        'after_coupon': after_coupon,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'catalog/cart_detail.html', context)

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
            request.session['coupon_percent'] = coupon.discount_percent
            request.session['coupon_applied'] = True
            # ====== این خط رو حذف کن (یا کامنت کن) ======
            # messages.success(request, f'کد تخفیف {code} با موفقیت اعمال شد.')
        except Coupon.DoesNotExist:
            messages.error(request, 'کد تخفیف نامعتبر است یا منقضی شده است.')
    return redirect('catalog:cart_detail')
    
def remove_coupon(request):
    if request.method == 'POST':
        request.session.pop('coupon_percent', None)
        request.session.pop('coupon_applied', None)
        messages.success(request, 'تخفیف با موفقیت لغو شد.')
    return redirect('catalog:cart_detail')


def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect('account:login')
    
    product = get_object_or_404(Product, id=product_id)
    wish = Wishlist.objects.filter(user=request.user, product=product)
    
    if wish.exists():
        wish.delete()
    else:
        Wishlist.objects.create(user=request.user, product=product)
    
    return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))


def send_share_email(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if email:
            try:
                send_mail(
                    f'اشتراک گذاری محصول: {product.title}',
                    f'این محصول رو ببین: {request.build_absolute_uri()}',
                    'noreply@yourdomain.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'ایمیل با موفقیت ارسال شد.')
            except Exception as e:
                messages.error(request, 'ارسال ایمیل با خطا مواجه شد.')
        else:
            messages.error(request, 'لطفا ایمیل را وارد کنید.')
    
    return redirect('catalog:product_detail', slug=product.slug)



def notify_me(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        method = request.POST.get('method')
        
        # اگر کاربر لاگین است
        if request.user.is_authenticated:
            email = request.user.email
            # شماره رو از پروفایل بگیر (اگه داری)
            phone = None
            if hasattr(request.user, 'profile') and request.user.profile.phone:
                phone = request.user.profile.phone
        else:
            email = request.POST.get('email')
            phone = request.POST.get('phone')
        
        # اعتبارسنجی
        if not method:
            messages.error(request, 'لطفاً یک روش اطلاع‌رسانی را انتخاب کنید.')
        elif method == 'email' and not email:
            messages.error(request, 'ایمیل خود را وارد کنید.')
        elif method == 'sms' and not phone:
            messages.error(request, 'شماره موبایل خود را وارد کنید.')
        else:
            ProductNotification.objects.create(
                product=product,
                method=method,
                email=email if method == 'email' else None,
                phone=phone if method == 'sms' else None,
            )
            messages.success(request, 'درخواست شما ثبت شد.')
    
    return redirect('catalog:product_detail', slug=product.slug)



def add_to_compare(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    compare_list = request.session.get('compare_list', [])
    if product_id not in compare_list:
        compare_list.append(product_id)
        request.session['compare_list'] = compare_list
        messages.success(request, 'محصول به لیست مقایسه اضافه شد.')
    else:
        messages.warning(request, 'این محصول قبلاً در لیست مقایسه است.')
    return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))


def remove_from_compare(request, product_id):
    compare_list = request.session.get('compare_list', [])
    if product_id in compare_list:
        compare_list.remove(product_id)
        request.session['compare_list'] = compare_list
    return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))

def comparison_page(request):
    compare_ids = request.session.get('compare_list', [])
    products = Product.objects.filter(id__in=compare_ids)
     # ====== اضافه کردن remaining_stock ======
    cart = request.session.get('cart', {})
    products = add_remaining_stock(products, cart)
    
    liked_products = []
    if request.user.is_authenticated:
        liked_products = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(
        request,
        'catalog/comparison.html',
        {
            'products': products,
            'liked_products': liked_products,
        }
    )




def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('variants'), slug=slug)

    color_id = request.GET.get('color')
    selected_variant = None
    if color_id:
        try:
            color_id = int(color_id)
            selected_variant = product.variants.filter(id=color_id).first()
        except ValueError:
            selected_variant = None
    if not selected_variant and product.variants.exists():
        selected_variant = product.variants.first()

    # ====== موجودی رنگ انتخاب‌شده ======
    stock = selected_variant.stock if selected_variant else product.stock

    # ====== تعداد موجود در سبد خرید برای همین رنگ ======
    cart = request.session.get('cart', {})
    cart_qty = 0
    if selected_variant:
        for key, item in cart.items():
            # اگر کلید ترکیبی است، product_id را از آن استخراج کن
            if '-' in key:
                product_id = int(key.split('-')[0])
            else:
                product_id = int(key)

            if product_id == product.id:
                if item.get('variant_id') == selected_variant.id:
                    cart_qty = item.get('quantity', 0)
                    break
    else:
        # اگر رنگی انتخاب نشده، کل محصول رو حساب کن
        for key, item in cart.items():
            if '-' in key:
                product_id = int(key.split('-')[0])
            else:
                product_id = int(key)
            if product_id == product.id:
                cart_qty = item.get('quantity', 0)
                break

    remaining_stock = stock - cart_qty


    # ====== محاسبه تخفیف ======
    discount = product.discounts.filter(
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).first()

    if discount:
        product.discount_percent = discount.discount_percent
        product.discounted_price = product.price - (product.price * discount.discount_percent // 100)
        product.discount_timestamp = int(discount.end_time.timestamp()) * 1000
    else:
        product.discount_percent = None
        product.discounted_price = None
        product.discount_timestamp = None

    # ====== کاربر و علاقه‌مندی ======
    user = request.user if request.user.is_authenticated else None
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Wishlist.objects.filter(user=request.user, product=product).exists()

    # ====== نظرات و امتیازات ======
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    form = ReviewForm()
    reviews = product.reviews.all()[:10]

    # ====== تبدیل تاریخ نظرات به فارسی ======
    persian_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    persian_months = {
        1: 'ژانویه', 2: 'فوریه', 3: 'مارس', 4: 'آوریل', 5: 'مه', 6: 'ژوئن',
        7: 'ژوئیه', 8: 'اوت', 9: 'سپتامبر', 10: 'اکتبر', 11: 'نوامبر', 12: 'دسامبر'
    }
    for review in reviews:
        day = review.created_at.day
        month_num = review.created_at.month
        year = review.created_at.year
        persian_day = str(day).translate(persian_digits)
        persian_month = persian_months[month_num]
        persian_year = str(year).translate(persian_digits)
        review.persian_date = f"{persian_day} {persian_month} {persian_year}"

    # ========== context ==========
    context = {
        'product': product,
        'user': user,
        'is_favorited': is_favorited,
        'avg_rating': avg_rating,
        'form': form,
        'reviews': reviews,
        'remaining_stock': remaining_stock,
        'stock':stock,
        'selected_variant': selected_variant,
        'discounted_price': product.discounted_price,
    }

    # ========== پیام‌های session ==========
    if 'product_message' in request.session:
        context['product_message'] = request.session.pop('product_message')
        context['message_type'] = request.session.pop('message_type')
        
    return render(request, 'catalog/product_detail.html', context)


@login_required
def submit_review(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if comment and comment.strip():
            Review.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={'rating': rating, 'comment': comment}
            )
    return redirect('catalog:product_detail', slug=product.slug)


@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    liked_products = wishlist_items.values_list('product_id', flat=True)
     # ====== دریافت سبد خرید ======
    cart = request.session.get('cart', {})
    compare_list = request.session.get('compare_list', [])

    # ====== اضافه کردن remaining_stock به هر محصول ======
    for item in wishlist_items:
        product = item.product

        # موجودی کل
        if product.variants.exists():
            total_stock = sum(variant.stock for variant in product.variants.all())
        else:
            total_stock = product.stock

        # تعداد در سبد خرید
        qty_in_cart = 0
        for key, cart_item in cart.items():
            if '-' in key:
                product_id = int(key.split('-')[0])
            else:
                product_id = int(key)
            if product_id == product.id:
                qty_in_cart += cart_item.get('quantity', 0)

        product.remaining_stock = total_stock - qty_in_cart
    

    return render(request, 'catalog/wishlist.html', {'wishlist_items': wishlist_items,"liked_products":liked_products, 'compare_list': compare_list,})

