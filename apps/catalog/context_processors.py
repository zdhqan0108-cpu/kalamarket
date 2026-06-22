from .models import Category
from apps.catalog.models import Wishlist,Product,ProductDiscount
from django.utils import timezone


def navbar_data(request):
    categories = Category.objects.prefetch_related('subcategories__brands', 'subcategories__product_type','subcategories__children','subcategories__children__children').all()
    return {
        'navbar_categories': categories,
    }

def cart_context(request):
    cart = request.session.get('cart', {})
    total = 0
    total_items = 0

    for key, item in cart.items():
        # استخراج product_id از کلید ترکیبی
        if '-' in key:
            product_id = int(key.split('-')[0])
        else:
            product_id = int(key)

        product = Product.objects.get(id=product_id)
        quantity = item.get('quantity', 0)
        price = int(product.price)

        # ====== محاسبه تخفیف محصول ======
        discount_obj = ProductDiscount.objects.filter(
            product=product,
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        if discount_obj:
            discount_percent = discount_obj.discount_percent
            discounted_price = price - (price * discount_percent // 100)
        else:
            discounted_price = price

        total_items += quantity
        total += discounted_price * quantity

    return {
        'total': total,
        'total_items': total_items,
    }


def wishlist_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    return {'wishlist_count': count}


    